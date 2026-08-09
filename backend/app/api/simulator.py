"""Fleet telemetry simulator control API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.runtime import get_store
from app.services import simulator_service as sim

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


@router.get("/status")
def simulator_status() -> dict:
    return sim.get_status()


@router.post("/start")
async def simulator_start() -> dict:
    store = get_store()
    result = await sim.start_simulator(store)
    if result.get("status") == "already_running":
        raise HTTPException(status_code=409, detail=result)
    return result


@router.post("/stop")
async def simulator_stop() -> dict:
    return await sim.stop_simulator()


@router.post("/reset")
async def simulator_reset() -> dict:
    store = get_store()
    return await sim.reset_simulator(store)
