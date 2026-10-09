"""FastAPI entry point: uvicorn app.main:app --host 0.0.0.0 --port 8000"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import jobs
from app.config import get_settings
from app.db import init_db
from app.routes import assets, health, lines, projects, renders

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.projects_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    jobs.recover_interrupted()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Brainrot Study API",
        version="0.1.0",
        lifespan=lifespan,
        # Nothing leaves the local network: switch off FastAPI's OpenTelemetry hooks entirely.
        telemetry={
            "tracing": False,
            "metrics": False,
            "logs": False,
            "operation_spans": False,
            "auto_configure": False,
        },
    )
    origins = [o.strip() for o in settings.api_cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    for module in (health, assets, projects, lines, renders):
        app.include_router(module.router)
    return app


app = create_app()
