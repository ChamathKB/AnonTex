import argparse
import logging
import os
import sys
from contextlib import asynccontextmanager

import aiohttp
import uvicorn
from fastapi import FastAPI, Request, Response

# Configure logging
logging.basicConfig(level=logging.INFO, format="[*] %(message)s")

app = FastAPI()

TARGET = "https://api.openai.com"  # Target server


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage aiohttp session lifecycle using asynccontextmanager."""
    global session
    session = aiohttp.ClientSession()
    yield
    await session.close()


app = FastAPI(lifespan=lifespan)

session: aiohttp.ClientSession = None


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
    logging.debug(f"Received {method} request from {request.client.host} to {url}, headers: {headers}")

    try:
        body = await request.body()
        async with session.request(method, url, headers=headers, data=body) as response:  # type: ignore
            response_body = await response.read()
            logging.info(f"Forwarded response from {url}, status: {response.status}")

            return Response(
                content=response_body,
                status_code=response.status,
                headers=dict(response.headers),
            )
    except Exception as e:
        logging.error(f"Error during proxying: {e}")
        return Response(content=f"Internal Server Error: {e}", status_code=500)


def run_server(port, daemon):
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
