"""Helpers for telemetry events (Pub/Sub push envelopes / raw JSON)."""

from __future__ import annotations

from typing import Any

from app.models.telemetry import TelemetrySample


def event_to_telemetry_sample(event: dict[str, Any]) -> TelemetrySample:
    """Map Pub/Sub event JSON to TelemetrySample."""
    payload = {
        "machine_id": event["machine_id"],
        "timestamp": event["timestamp"],
        "temperature_c": event.get("temperature_c", event.get("temperature")),
        "vibration_mm_s": event.get("vibration_mm_s", event.get("vibration")),
        "motor_current_a": event.get(
            "motor_current_a", event.get("motor_current")
        ),
    }
    return TelemetrySample.model_validate(payload)
