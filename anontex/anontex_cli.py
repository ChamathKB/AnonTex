import logging
from contextlib import asynccontextmanager
from pathlib import Path

import aiohttp
import click
import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from pydantic import ValidationError

from anontex.constants import DEFAULT_CONFIG_PATH, REDIS_URL
from anontex.routes.openai_proxy import create_router

logging.basicConfig(level=logging.INFO, format="[*] %(message)s")
logger = logging.getLogger(__name__)


def create_app(config_path: Path) -> FastAPI:
    """Application factory"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage the lifespan of the application."""
        logging.info("Starting up resources...")
        provider = NlpEngineProvider(conf_file=config_path)
        app.state.analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
        app.state.anonymizer = AnonymizerEngine()
        app.state.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # global session
        # session = aiohttp.ClientSession()
        app.state.session = aiohttp.ClientSession()
        yield
        logging.info("Shutting down resources...")
        await app.state.redis_client.close()
        await app.state.session.close()

    app = FastAPI(lifespan=lifespan)
    return app


@click.group()
def anontex():
    """Main CLI group for the application."""
    pass


@anontex.command()
def version() -> None:
    """Display the version of the application."""
    click.echo("AnonTex v0.1.0")
    return


@anontex.command()
@click.option("--config", type=click.Path(exists=True, path_type=Path), required=True, default=DEFAULT_CONFIG_PATH)
@click.option("--port", type=int, default=8000)
@click.option("--host", type=str, default="0.0.0.0")
def run(config: Path, port: int, host: str):
    """Main entry point for the anonymization service"""
    try:
        app = create_app(config_path=config)
        router = create_router(app)
        app.include_router(router)
        logging.info(f"Starting FastAPI server on port {port}")
        uvicorn.run(app, host=host, port=port, log_level="debug")
    except ValidationError as e:
        logger.error(f"Configuration error: {e}")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise click.Abort()


if __name__ == "__main__":
    # anontex.add_command(version)
    # anontex.add_command(main)
    anontex()
