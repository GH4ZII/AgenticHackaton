"""Telemetry tools backed by the in-memory domain store."""

from __future__ import annotations

from app.models.telemetry import TelemetrySample
from app.runtime import get_store


def _trend_label(values: list[float]) -> str:
    if len(values) < 2:
        return "insufficient_data"
    delta = values[-1] - values[0]
    if delta > 2.0:
        return "increasing_sharply" if delta > 5.0 else "increasing"
    if delta < -2.0:
        return "decreasing"
    return "stable"


def _build_trend(samples: list[TelemetrySample]) -> dict:
    temps = [s.temperature_c for s in samples]
    vibs = [s.vibration_mm_s for s in samples]
    currents = [s.motor_current_a for s in samples]
    latest = samples[-1]
    summary_parts = [
        f"Latest vibration {latest.vibration_mm_s} mm/s,",
        f"temperature {latest.temperature_c} C,",
        f"motor current {latest.motor_current_a} A.",
    ]
    return {
        "temperature_c": _trend_label(temps),
        "vibration_mm_s": _trend_label(vibs),
        "motor_current_a": _trend_label(currents),
        "summary": " ".join(summary_parts),
    }


def get_telemetry_history(machine_id: str) -> dict:
    """Get recent telemetry samples and trend for a machine.

    Use this when investigating abnormal machine behavior to inspect
    temperature, vibration, and motor current over time.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".

    Returns:
        Telemetry history dictionary, or a not-found status payload.
    """
    store = get_store()
    machine = store.get_machine(machine_id)
    samples = store.get_telemetry_for_machine(machine_id)
    if machine is None and not samples:
        return {
            "status": "not_found",
            "machine_id": machine_id,
            "message": f"No telemetry history found for '{machine_id}'.",
        }

    ordered = sorted(samples, key=lambda s: s.timestamp)
    payload_samples = [
        {
            "timestamp": sample.timestamp.isoformat().replace("+00:00", "Z"),
            "temperature_c": sample.temperature_c,
            "vibration_mm_s": sample.vibration_mm_s,
            "motor_current_a": sample.motor_current_a,
        }
        for sample in ordered
    ]

    return {
        "status": "success",
        "telemetry": {
            "machine_id": machine_id.strip().upper(),
            "samples": payload_samples,
            "trend": _build_trend(ordered) if ordered else {},
        },
    }
