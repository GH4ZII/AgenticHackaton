"""Machine tools backed by the domain store."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.machine import MachineStatus
from app.runtime import get_store


def get_machine_context(machine_id: str) -> dict:
    """Get metadata and normal operating limits for a machine.

    Use this when investigating a machine to learn its type, manufacturer,
    model, normal limits, and current status before diagnosing a fault.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".

    Returns:
        Machine context dictionary, or a not-found status payload.
    """
    store = get_store()
    machine = store.get_machine(machine_id)
    if machine is None:
        return {
            "status": "not_found",
            "machine_id": machine_id,
            "message": f"No machine context found for '{machine_id}'.",
        }

    return {
        "status": "success",
        "machine": {
            "machine_id": machine.machine_id,
            "name": machine.name,
            "machine_type": machine.machine_type,
            "manufacturer": machine.manufacturer,
            "model": machine.model,
            "location": machine.location,
            "status": machine.status.value,
            "normal_operating_limits": {
                "temperature_c": {"max": machine.temperature_limit},
                "vibration_mm_s": {"max": machine.vibration_limit},
                "motor_current_a": {"max": machine.motor_current_limit},
            },
            "notes": machine.notes,
        },
    }


def update_machine_status(machine_id: str, status: str) -> dict:
    """Update the operational status of a machine.

    Use after diagnosing an incident to reflect health, for example
    MAINTENANCE_REQUIRED when a high-severity fault needs repair.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".
        status: One of HEALTHY, MONITORING, WARNING, MAINTENANCE_REQUIRED,
            OUT_OF_SERVICE.

    Returns:
        Updated machine status payload, or an error payload.
    """
    store = get_store()
    machine = store.get_machine(machine_id)
    if machine is None:
        return {
            "status": "not_found",
            "machine_id": machine_id,
            "message": f"No machine found for '{machine_id}'.",
        }

    normalized = status.strip().upper()
    try:
        machine.status = MachineStatus(normalized)
    except ValueError:
        allowed = ", ".join(s.value for s in MachineStatus)
        return {
            "status": "error",
            "machine_id": machine_id,
            "message": f"Invalid status '{status}'. Allowed: {allowed}.",
        }

    store.upsert_machine(machine)
    open_incident = store.get_open_incident_for_machine(machine.machine_id)
    store.add_agent_action(
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "machine_id": machine.machine_id,
            "incident_id": open_incident.incident_id if open_incident else None,
            "action": "machine_status_updated",
            "detail": f"Machine status set to {machine.status.value}",
        }
    )
    return {
        "status": "success",
        "machine_id": machine.machine_id,
        "new_status": machine.status.value,
    }
