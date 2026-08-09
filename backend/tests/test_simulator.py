"""Fleet telemetry simulator API and service tests."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.incident import IncidentStatus
from app.models.machine import MachineStatus
from app.seed import seed_store
from app.services import simulator_service as sim


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("USE_FIRESTORE", "false")
    domain = seed_store()
    monkeypatch.setattr("app.runtime.STORE", domain)
    sim.reset_config()
    sim.set_config(invoke_agent=False, tick_interval_s=0.05)

    try:
        with TestClient(app) as test_client:
            yield test_client, domain
    finally:
        asyncio.run(sim.reset_simulator(domain))
        sim.reset_config()


def test_simulator_start_stop_status(client):
    test_client, _domain = client

    idle = test_client.get("/api/simulator/status")
    assert idle.status_code == 200
    assert idle.json()["running"] is False

    started = test_client.post("/api/simulator/start")
    assert started.status_code == 200
    body = started.json()
    assert body["status"] == "started"
    assert body["running"] is True
    assert body["phase"] in {"healthy", "degrading"}

    conflict = test_client.post("/api/simulator/start")
    assert conflict.status_code == 409

    stopped = test_client.post("/api/simulator/stop")
    assert stopped.status_code == 200
    assert stopped.json()["running"] is False


def test_simulator_reset_clears_open_work(client):
    test_client, domain = client

    demo = test_client.post("/api/demo/seed")
    assert demo.status_code == 200
    assert domain.get_machine("PUMP-04").status != MachineStatus.HEALTHY

    reset = test_client.post("/api/simulator/reset")
    assert reset.status_code == 200
    assert reset.json()["running"] is False
    assert reset.json()["phase"] == "idle"

    for machine in domain.machines.values():
        assert machine.status == MachineStatus.HEALTHY

    open_incidents = [
        i for i in domain.list_incidents() if i.status != IncidentStatus.RESOLVED
    ]
    assert open_incidents == []


@pytest.mark.asyncio
async def test_forced_failure_creates_incident(store, monkeypatch):
    monkeypatch.setenv("USE_FIRESTORE", "false")
    sim.reset_config()
    sim.set_config(
        invoke_agent=False,
        tick_interval_s=0.01,
        healthy_window_ticks=0,
        fail_probability=0.0,
        ramp_ticks=4,
    )

    try:
        await sim.reset_simulator(store)
        sim.prepare_fleet(store)
        # Drive ticks without starting the background loop (deterministic).
        sim._state.running = True
        sim._state.ticks = 0
        sim._state.phase = "healthy"
        sim._state.active_failures = []

        sim.schedule_failure("FAN-01", mode="imbalance", ramp_ticks=4)

        for _ in range(8):
            await sim._tick(store)

        status = sim.get_status()
        assert any(f["machine_id"] == "FAN-01" for f in status["active_failures"])

        open_incident = store.get_open_incident_for_machine("FAN-01")
        assert open_incident is not None
        assert store.get_machine("FAN-01").status == MachineStatus.WARNING
    finally:
        sim._state.running = False
        sim._state.phase = "idle"
        sim._state.active_failures = []
        sim.reset_config()


@pytest.mark.asyncio
async def test_seed_pump_starts_healthy(store):
    machine = store.get_machine("PUMP-04")
    assert machine is not None
    assert machine.status == MachineStatus.HEALTHY
