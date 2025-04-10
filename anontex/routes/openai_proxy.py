import json
import logging

from fastapi import APIRouter, FastAPI, Request, Response

from anontex.constants import ENTITY_LIST, LANGUAGE, TARGET
from anontex.engines import anonymize_text, deanonymize_text


def create_router(app: FastAPI) -> APIRouter:
    router = APIRouter()

    @router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    async def reverse_proxy(request: Request, path: str) -> Response:
        """
        Generic reverse proxy endpoint that forwards requests to the target server.
        """
        url = f"{TARGET}/{path}"
        headers = {
            "content-type": request.headers.get("content-type"),
            "authorization": request.headers.get("authorization"),
        }
        method = request.method
        data = await request.json()
        session = app.state.session
        if "messages" not in data or not isinstance(data["messages"], list) or not data["messages"]:
            try:
                async with session.request(method, url, headers=headers, json=data) as response:  # type: ignore
                    response_body = await response.read()
                    return Response(content=response_body, status_code=response.status, headers=dict(response.headers))
            except Exception as e:
                logging.error(f"⚠️ Error during proxying: {e}")
                return Response(content=f"Internal Server Error: {e}", status_code=500)

        logging.debug(f"🔍️ Received {method} request from {request.client.host} to {url}, headers: {headers}")

        anonymized_message, request_id = await anonymize_text(request, app, entities=ENTITY_LIST, language=LANGUAGE)

        data["messages"][-1]["content"] = anonymized_message

        try:
            async with session.request(method, url, headers=headers, json=data) as response:  # type: ignore
                response_body = await response.read()
                logging.info(f"ℹ️ Forwarded response from {url}, status: {response.status}")
                if response.status != 200:
                    return Response(content=response_body, status_code=response.status, headers=dict(response.headers))

                response_body = json.loads(response_body.decode("utf-8"))

                response_content = response_body.get("choices", [{}])[0].get("message", {}).get("content", "")
                logging.debug(f"🔍️ Received response content: {response_content[:100]}...")

                deanonymized_message = await deanonymize_text(response_content, app, request_id)

                if "choices" in response_body and len(response_body["choices"]) > 0:
                    if "message" in response_body["choices"][0]:
                        response_body["choices"][0]["message"]["content"] = deanonymized_message

                logging.debug(f"🔍️ Deanonymized response: {deanonymized_message[:100]}...")

                return Response(
                    content=json.dumps(response_body),
                    status_code=response.status,
                    headers=dict(response.headers),
                )
        except Exception as e:
            logging.error(f"⚠️ Error during proxying: {e}")
            return Response(content=f"Internal Server Error: {e}", status_code=500)

    return router
