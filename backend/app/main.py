"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.approvals import router as approvals_router
from app.api.demo import router as demo_router
from app.api.events import router as events_router
from app.api.incidents import router as incidents_router
from app.api.machines import router as machines_router
from app.api.ops import router as ops_router
from app.api.work_orders import router as work_orders_router

app = FastAPI(
    title="Maintenance Agent API",
    description="Telemetry events and maintenance workflow backend",
    version="0.9.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
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
