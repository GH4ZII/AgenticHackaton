"""Maintenance history tools backed by the in-memory domain store."""

from __future__ import annotations

from app.runtime import get_store


def get_maintenance_history(machine_id: str) -> dict:
    """Get previous services, replacements, faults, and inspections.

    Use this when diagnosing a machine to learn what work was done before
    and whether similar faults have occurred.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".

    Returns:
        Maintenance history dictionary, or a not-found status payload.
    """
    store = get_store()
    machine = store.get_machine(machine_id)
    history = store.get_maintenance_history(machine_id)
    if machine is None and not history:
        return {
            "status": "not_found",
            "machine_id": machine_id,
            "message": f"No maintenance history found for '{machine_id}'.",
        }

    return {
        "status": "success",
        "machine_id": machine_id.strip().upper(),
        "history": history,
        "last_inspection": next(
            (entry for entry in reversed(history) if entry.get("type") == "inspection"),
            None,
        ),
    }
