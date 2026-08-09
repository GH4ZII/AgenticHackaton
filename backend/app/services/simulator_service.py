"""Continuous fleet telemetry simulator with random failure ramps."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from app.models.incident import IncidentStatus
from app.models.machine import Machine, MachineStatus
from app.models.telemetry import TelemetrySample
from app.models.work_order import WorkOrderStatus
from app.services.incident_workflow import handle_telemetry
from app.store.protocol import DomainStore

FailureMode = Literal["bearing_degradation", "overheating", "imbalance"]

FAILURE_MODES: tuple[FailureMode, ...] = (
    "bearing_degradation",
    "overheating",
    "imbalance",
)


@dataclass
class SimulatorConfig:
    tick_interval_s: float = 2.0
    healthy_window_ticks: int = 3  # ~6s at 2s ticks
    fail_probability: float = 0.22  # chance per tick after window
    ramp_ticks: int = 16  # ~32s to exceed limits
    invoke_agent: bool = True


@dataclass
class ActiveFailure:
    machine_id: str
    mode: FailureMode
    started_tick: int
    ramp_ticks: int

    def progress(self, current_tick: int) -> float:
        elapsed = max(0, current_tick - self.started_tick)
        return min(1.0, elapsed / max(1, self.ramp_ticks))


@dataclass
class SimulatorState:
    running: bool = False
    started_at: str | None = None
    ticks: int = 0
    phase: str = "idle"
    active_failures: list[ActiveFailure] = field(default_factory=list)
    last_error: str | None = None


_config = SimulatorConfig()
_state = SimulatorState()
_task: asyncio.Task[None] | None = None
_lock = asyncio.Lock()


def get_config() -> SimulatorConfig:
    return _config


def set_config(**kwargs: Any) -> SimulatorConfig:
    """Update simulator timing knobs (used by tests)."""
    global _config
    data = {
        "tick_interval_s": _config.tick_interval_s,
        "healthy_window_ticks": _config.healthy_window_ticks,
        "fail_probability": _config.fail_probability,
        "ramp_ticks": _config.ramp_ticks,
        "invoke_agent": _config.invoke_agent,
    }
    data.update(kwargs)
    _config = SimulatorConfig(**data)
    return _config


def reset_config() -> SimulatorConfig:
    global _config
    _config = SimulatorConfig()
    return _config


def get_status() -> dict[str, Any]:
    return {
        "running": _state.running,
        "phase": _state.phase,
        "ticks": _state.ticks,
        "started_at": _state.started_at,
        "active_failures": [
            {
                "machine_id": f.machine_id,
                "mode": f.mode,
                "progress": round(f.progress(_state.ticks), 3),
            }
            for f in _state.active_failures
        ],
        "last_error": _state.last_error,
    }


def _list_machines(store: DomainStore) -> list[Machine]:
    machines_attr = getattr(store, "machines", None)
    if isinstance(machines_attr, dict):
        return list(machines_attr.values())
    if hasattr(store, "client"):
        return [
            Machine.model_validate(doc.to_dict())
            for doc in store.client.collection("machines").stream()
        ]
    return []


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat().replace("+00:00", "Z")


def prepare_fleet(store: DomainStore) -> None:
    """Set all machines healthy and clear open incidents / work orders."""
    for machine in _list_machines(store):
        machine.status = MachineStatus.HEALTHY
        store.upsert_machine(machine)

    for incident in store.list_incidents():
        if incident.status != IncidentStatus.RESOLVED:
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = _now()
            store.add_incident(incident)

    for work_order in store.list_work_orders():
        if work_order.status not in {
            WorkOrderStatus.COMPLETED,
            WorkOrderStatus.CANCELLED,
        }:
            work_order.status = WorkOrderStatus.CANCELLED
            store.upsert_work_order(work_order)


def _failure_for(machine_id: str) -> ActiveFailure | None:
    for failure in _state.active_failures:
        if failure.machine_id == machine_id:
            return failure
    return None


def schedule_failure(
    machine_id: str,
    mode: FailureMode | None = None,
    *,
    ramp_ticks: int | None = None,
) -> ActiveFailure:
    """Start (or replace) a failure ramp for a machine. Used by loop + tests."""
    existing = _failure_for(machine_id)
    if existing is not None:
        return existing
    failure = ActiveFailure(
        machine_id=machine_id.strip().upper(),
        mode=mode or random.choice(FAILURE_MODES),
        started_tick=_state.ticks,
        ramp_ticks=ramp_ticks if ramp_ticks is not None else _config.ramp_ticks,
    )
    _state.active_failures.append(failure)
    _state.phase = "degrading"
    return failure


def _maybe_schedule_random_failure(store: DomainStore) -> None:
    if _state.ticks < _config.healthy_window_ticks:
        return
    if random.random() > _config.fail_probability:
        return

    candidates = [
        m.machine_id
        for m in _list_machines(store)
        if _failure_for(m.machine_id) is None
        and store.get_open_incident_for_machine(m.machine_id) is None
    ]
    if not candidates:
        return
    schedule_failure(random.choice(candidates))


def _healthy_sample(machine: Machine) -> TelemetrySample:
    # Stay ~70–90% of each limit with light jitter.
    return TelemetrySample(
        machine_id=machine.machine_id,
        timestamp=_now(),
        temperature_c=round(
            machine.temperature_limit * random.uniform(0.55, 0.82), 2
        ),
        vibration_mm_s=round(
            machine.vibration_limit * random.uniform(0.35, 0.75), 2
        ),
        motor_current_a=round(
            machine.motor_current_limit * random.uniform(0.45, 0.8), 2
        ),
    )


def _degraded_sample(machine: Machine, failure: ActiveFailure) -> TelemetrySample:
    progress = failure.progress(_state.ticks)
    # Ease from ~0.75× limit toward 1.15–1.35× depending on mode.
    base_t = machine.temperature_limit * 0.75
    base_v = machine.vibration_limit * 0.7
    base_c = machine.motor_current_limit * 0.75

    if failure.mode == "bearing_degradation":
        peak_t = machine.temperature_limit * 1.22
        peak_v = machine.vibration_limit * 1.35
        peak_c = machine.motor_current_limit * 1.18
    elif failure.mode == "overheating":
        peak_t = machine.temperature_limit * 1.35
        peak_v = machine.vibration_limit * 1.05
        peak_c = machine.motor_current_limit * 1.12
    else:  # imbalance
        peak_t = machine.temperature_limit * 1.08
        peak_v = machine.vibration_limit * 1.4
        peak_c = machine.motor_current_limit * 1.1

    temp = base_t + (peak_t - base_t) * progress
    vib = base_v + (peak_v - base_v) * progress
    current = base_c + (peak_c - base_c) * progress

    # Small noise; clamp noise so we still trend upward.
    temp += random.uniform(-0.4, 0.6)
    vib += random.uniform(-0.05, 0.08)
    current += random.uniform(-0.1, 0.15)

    return TelemetrySample(
        machine_id=machine.machine_id,
        timestamp=_now(),
        temperature_c=round(temp, 2),
        vibration_mm_s=round(vib, 2),
        motor_current_a=round(current, 2),
    )


def build_sample(machine: Machine) -> TelemetrySample:
    failure = _failure_for(machine.machine_id)
    if failure is None:
        return _healthy_sample(machine)
    return _degraded_sample(machine, failure)


async def _tick(store: DomainStore) -> None:
    _state.ticks += 1
    if not _state.active_failures and _state.ticks < _config.healthy_window_ticks:
        _state.phase = "healthy"
    _maybe_schedule_random_failure(store)

    for machine in _list_machines(store):
        sample = build_sample(machine)
        await handle_telemetry(
            store,
            sample,
            invoke_agent=_config.invoke_agent,
        )

    if _state.active_failures:
        _state.phase = "degrading"
    elif _state.running:
        _state.phase = "healthy"


async def _run_loop(store: DomainStore) -> None:
    try:
        while _state.running:
            await _tick(store)
            await asyncio.sleep(_config.tick_interval_s)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 — keep loop status visible
        _state.last_error = str(exc)
        _state.running = False
        _state.phase = "error"
        raise
    finally:
        if not _state.running and _state.phase not in {"error", "idle"}:
            _state.phase = "stopped"


async def start_simulator(store: DomainStore) -> dict[str, Any]:
    global _task
    async with _lock:
        if _state.running and _task is not None and not _task.done():
            return {
                "status": "already_running",
                **get_status(),
            }

        prepare_fleet(store)
        _state.running = True
        _state.started_at = _now_iso()
        _state.ticks = 0
        _state.phase = "healthy"
        _state.active_failures = []
        _state.last_error = None

        _task = asyncio.create_task(_run_loop(store), name="fleet-simulator")
        return {"status": "started", **get_status()}


async def stop_simulator() -> dict[str, Any]:
    global _task
    async with _lock:
        _state.running = False
        task = _task
        _task = None

    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    if _state.phase not in {"error"}:
        _state.phase = "stopped"
    return {"status": "stopped", **get_status()}


async def reset_simulator(store: DomainStore) -> dict[str, Any]:
    await stop_simulator()
    prepare_fleet(store)
    _state.ticks = 0
    _state.active_failures = []
    _state.started_at = None
    _state.phase = "idle"
    _state.last_error = None
    return {"status": "reset", **get_status()}
