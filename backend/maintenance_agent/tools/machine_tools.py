"""Fake machine tools for Phase 1 local ADK testing."""

from __future__ import annotations


_PUMP_04 = {
    "machine_id": "PUMP-04",
    "name": "Cooling Water Pump 04",
    "machine_type": "centrifugal_pump",
    "manufacturer": "FlowTech Industrial",
    "model": "FT-C200",
    "location": "Plant A / Cooling Loop 2",
    "normal_operating_limits": {
        "temperature_c": {"min": 40, "max": 70},
        "vibration_mm_s": {"min": 0.5, "max": 4.5},
        "motor_current_a": {"min": 8, "max": 12.5},
    },
    "status": "WARNING",
    "notes": "Drive-end bearing area flagged for elevated vibration.",
}


def get_machine_context(machine_id: str) -> dict:
    """Get metadata and normal operating limits for a machine.

    Use this when investigating a machine to learn its type, manufacturer,
    model, normal limits, and current status before diagnosing a fault.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".

    Returns:
        Machine context dictionary, or a not-found status payload.
    """
    normalized = machine_id.strip().upper()
    if normalized == "PUMP-04":
        return {"status": "success", "machine": _PUMP_04}

    return {
        "status": "not_found",
        "machine_id": machine_id,
        "message": f"No machine context found for '{machine_id}'.",
    }
