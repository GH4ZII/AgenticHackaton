"""Fake telemetry tools for Phase 1 local ADK testing."""

from __future__ import annotations


_PUMP_04_HISTORY = {
    "machine_id": "PUMP-04",
    "samples": [
        {
            "timestamp": "2026-08-07T08:00:00Z",
            "temperature_c": 62.0,
            "vibration_mm_s": 3.1,
            "motor_current_a": 11.0,
        },
        {
            "timestamp": "2026-08-07T09:00:00Z",
            "temperature_c": 66.0,
            "vibration_mm_s": 3.8,
            "motor_current_a": 11.5,
        },
        {
            "timestamp": "2026-08-07T10:00:00Z",
            "temperature_c": 71.0,
            "vibration_mm_s": 5.4,
            "motor_current_a": 12.8,
        },
        {
            "timestamp": "2026-08-07T11:00:00Z",
            "temperature_c": 78.0,
            "vibration_mm_s": 7.2,
            "motor_current_a": 13.5,
        },
        {
            "timestamp": "2026-08-07T12:00:00Z",
            "temperature_c": 86.0,
            "vibration_mm_s": 8.7,
            "motor_current_a": 14.0,
        },
    ],
    "trend": {
        "temperature_c": "increasing",
        "vibration_mm_s": "increasing_sharply",
        "motor_current_a": "increasing",
        "summary": (
            "Vibration, temperature, and motor current are all rising. "
            "Latest vibration 8.7 mm/s and temperature 86 C exceed normal limits."
        ),
    },
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
    normalized = machine_id.strip().upper()
    if normalized == "PUMP-04":
        return {"status": "success", "telemetry": _PUMP_04_HISTORY}

    return {
        "status": "not_found",
        "machine_id": machine_id,
        "message": f"No telemetry history found for '{machine_id}'.",
    }
