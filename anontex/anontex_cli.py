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
from pydantic import ValidationError

from anontex.constants import DEFAULT_CONFIG_PATH, LOG_LEVELS, REDIS_URL
from anontex.routes.openai_proxy import create_router


def create_app(config_path: Path) -> FastAPI:
    """Application factory"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage the lifespan of the application."""
        logging.info("🟢️ Starting up resources...")
        provider = NlpEngineProvider(conf_file=config_path)
        app.state.analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
        app.state.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        app.state.session = aiohttp.ClientSession()
        yield
        logging.info("🔴️ Shutting down resources...")
        await app.state.redis_client.aclose()
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
    from importlib.metadata import version

    PACKAGE = "anontex"
    click.echo(f"🎭️ AnonTex v{version(PACKAGE)}")
    return


@anontex.command()
@click.option("--config", type=click.Path(exists=True, path_type=Path), required=True, default=DEFAULT_CONFIG_PATH)
@click.option("--host", type=str, default="0.0.0.0")
@click.option("--port", type=int, default=8000)
@click.option("--log-level", type=click.Choice(LOG_LEVELS.keys()), default="info")
def run(config: Path, port: int, host: str, log_level: str):
    """Main entry point for the anonymization service"""
    logging.basicConfig(level=LOG_LEVELS[log_level.lower()], format="[*] %(message)s")
    logger = logging.getLogger(__name__)
    try:
        app = create_app(config_path=config)
        router = create_router(app)
        app.include_router(router)
        logging.info(f"⚙️ Starting FastAPI server on port {port}")
        uvicorn.run(app, host=host, port=port, log_level=log_level)
    except ValidationError as e:
        logger.error(f"❌️ Configuration error: {e}")
        raise click.Abort()
    except Exception as e:
        logger.error(f"❌️ Failed to start service: {e}")
        raise click.Abort()


if __name__ == "__main__":
    anontex()
