"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.events import router as events_router

app = FastAPI(
    title="Maintenance Agent API",
    description="Telemetry events and maintenance workflow backend",
    version="0.6.0",
)
app.include_router(events_router)
