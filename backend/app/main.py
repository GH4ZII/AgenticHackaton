"""FastAPI application entrypoint."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.approvals import router as approvals_router
from app.api.demo import router as demo_router
from app.api.events import router as events_router
from app.api.incidents import router as incidents_router
from app.api.machines import router as machines_router
from app.api.ops import router as ops_router
from app.api.simulator import router as simulator_router
from app.api.work_orders import router as work_orders_router

app = FastAPI(
    title="Maintenance Agent API",
    description="Telemetry events and maintenance workflow backend",
    version="0.10.0",
)

_LOCAL_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

_extra = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_LOCAL_ORIGINS + _extra,
    allow_origin_regex=r"https://.*\.run\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router)
app.include_router(machines_router)
app.include_router(incidents_router)
app.include_router(work_orders_router)
app.include_router(approvals_router)
app.include_router(ops_router)
app.include_router(demo_router)
app.include_router(simulator_router)

_static_dir = Path(os.getenv("STATIC_DIR", "static")).resolve()
_index_html = _static_dir / "index.html"

if _index_html.is_file():
    assets_dir = _static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def spa_index() -> FileResponse:
        return FileResponse(_index_html)

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        """Serve built SPA assets / index for client-side routes."""
        candidate = (_static_dir / full_path).resolve()
        if (
            candidate.is_file()
            and str(candidate).startswith(str(_static_dir))
            and full_path
            and not full_path.startswith(("api/", "events/", "docs", "openapi", "redoc"))
        ):
            return FileResponse(candidate)
        return FileResponse(_index_html)
