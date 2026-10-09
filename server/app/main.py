"""FastAPI entry point: uvicorn app.main:app --host 0.0.0.0 --port 8000

The REST API lives under /api. When the web app has been built (apps/web/dist),
it is served from the same server at /, so phones and laptops on the Wi-Fi just
open http://<laptop-ip>:8000.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import jobs
from app.config import get_settings
from app.db import init_db
from app.routes import assets, health, lines, projects, renders
from app.schemas import API_PREFIX

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.projects_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    jobs.recover_interrupted()
    yield


def mount_web_app(app: FastAPI, dist: Path) -> None:
    """Serve the built single-page app: real files as-is, every other path gets index.html."""
    index = dist / "index.html"
    root = dist.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def web_app(path: str) -> FileResponse:
        if path.startswith(API_PREFIX.lstrip("/") + "/") or path == API_PREFIX.lstrip("/"):
            raise HTTPException(404, "Not found")
        candidate = (dist / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            # Hashed build assets never change; index.html must always be fresh.
            cache = "public, max-age=31536000, immutable" if "/assets/" in f"/{path}" else "no-cache"
            return FileResponse(candidate, headers={"Cache-Control": cache})
        return FileResponse(index, headers={"Cache-Control": "no-cache"})


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Brainrot Study API",
        version="0.2.0",
        lifespan=lifespan,
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
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
        app.include_router(module.router, prefix=API_PREFIX)
    if (settings.web_dist_dir / "index.html").is_file():
        mount_web_app(app, settings.web_dist_dir)
    return app


app = create_app()
