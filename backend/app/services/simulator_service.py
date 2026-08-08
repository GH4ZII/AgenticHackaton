"""Simple telemetry event builder / publisher for demos (Phase 6)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from app.services.pubsub_service import publish_telemetry

Scenario = Literal[
    "NORMAL_OPERATION",
    "BEARING_DEGRADATION",
    "OVERHEATING",
    "SENSOR_SPIKE",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_telemetry_event(
    scenario: Scenario = "BEARING_DEGRADATION",
    *,
    machine_id: str = "PUMP-04",
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Build a Pub/Sub telemetry payload in project-plan field names."""
    ts = timestamp or _now_iso()
    if scenario == "NORMAL_OPERATION":
        return {
            "machine_id": machine_id,
            "timestamp": ts,
            "temperature": 62.0,
            "vibration": 3.0,
            "motor_current": 11.0,
        }
    if scenario == "OVERHEATING":
        return {
            "machine_id": machine_id,
            "timestamp": ts,
            "temperature": 92.0,
            "vibration": 3.5,
            "motor_current": 12.0,
        }
    if scenario == "SENSOR_SPIKE":
        return {
            "machine_id": machine_id,
            "timestamp": ts,
            "temperature": 64.0,
            "vibration": 12.0,
            "motor_current": 11.2,
        }
    # BEARING_DEGRADATION climax (primary demo)
    return {
        "machine_id": machine_id,
        "timestamp": ts,
        "temperature": 86.0,
        "vibration": 8.7,
        "motor_current": 14.1,
    }


def publish_scenario(
    scenario: Scenario = "BEARING_DEGRADATION",
    *,
    machine_id: str = "PUMP-04",
) -> tuple[str, dict[str, Any]]:
    """Publish a scenario event to Pub/Sub. Returns (message_id, event)."""
    event = build_telemetry_event(scenario, machine_id=machine_id)
    message_id = publish_telemetry(event)
    return message_id, event
