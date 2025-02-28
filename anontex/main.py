import argparse
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

import aiohttp

# import aioredis
import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from anontex.constants import REDIS_URL, TARGET
from anontex.engines import anonymize_text, deanonymize_text  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO, format="[*] %(message)s")


session: Optional[aiohttp.ClientSession] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifespan of the application."""
    logging.info("Starting up resources...")
    app.state.analyzer = AnalyzerEngine()
    app.state.anonymizer = AnonymizerEngine()
    app.state.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    global session
    session = aiohttp.ClientSession()
    yield
    logging.info("Shutting down resources...")
    await app.state.redis_client.close()
    await session.close()


app = FastAPI(lifespan=lifespan)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
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

    if "messages" not in data or not isinstance(data["messages"], list) or not data["messages"]:
        raise HTTPException(status_code=400, detail="Invalid messages format.")

    logging.debug(f"Received {method} request from {request.client.host} to {url}, headers: {headers}")

    anonymized_message, request_id = await anonymize_text(
        request, app, entities=["PHONE_NUMBER", "PERSON"], language="en"  # type: ignore
    )

    data["messages"][-1]["content"] = anonymized_message

    try:
        async with session.request(method, url, headers=headers, json=data) as response:  # type: ignore
            response_body = await response.read()
            logging.info(f"Forwarded response from {url}, status: {response.status}")
            response_body = json.loads(response_body.decode("utf-8"))

            # Extract the content from the response
            response_content = response_body.get("choices", [{}])[0].get("message", {}).get("content", "")
            logging.debug(f"Received response content: {response_content[:100]}...")
            # Deanonymize the response content
            deanonymized_message = await deanonymize_text(response_content, app, request_id)

            # Update the response with deanonymized content
            if "choices" in response_body and len(response_body["choices"]) > 0:
                if "message" in response_body["choices"][0]:
                    response_body["choices"][0]["message"]["content"] = deanonymized_message

            logging.debug(f"Deanonymized response: {deanonymized_message[:100]}...")

            return Response(
                content=json.dumps(response_body),
                status_code=response.status,
                headers=dict(response.headers),
            )
    except Exception as e:
        logging.error(f"Error during proxying: {e}")
        return Response(content=f"Internal Server Error: {e}", status_code=500)


def run_server(port: int, daemon: bool) -> None:
    """
    Starts the FastAPI server with optional daemonization.
    """
    if daemon:
        pid = os.fork()
        if pid > 0:  # Parent process
            logging.info(f"Daemon started with PID {pid}")
            sys.exit(0)

    logging.info(f"Starting FastAPI server on port {port}, daemon mode: {daemon}")
    uvicorn.run("proxy:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="FastAPI Reverse Proxy Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--daemon", action="store_true", help="Run as a daemon (background process)")
    args = parser.parse_args()

    run_server(args.port, args.daemon)
