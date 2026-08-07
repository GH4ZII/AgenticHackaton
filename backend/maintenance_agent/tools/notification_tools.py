"""Notification tools backed by the in-memory domain store."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.runtime import get_store


def notify_technician(
    machine_id: str,
    message: str,
    priority: str = "HIGH",
    technician: str = "on-call",
) -> dict:
    """Create a simulated technician notification.

    Use this for HIGH or CRITICAL incidents after diagnosis. Does not send
    real SMS or email; stores a notification for the dashboard / demo.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".
        message: Notification body for the technician.
        priority: Priority label such as MEDIUM, HIGH, or URGENT.
        technician: Recipient label, defaults to on-call.

    Returns:
        Created notification payload.
    """
    store = get_store()
    machine = store.get_machine(machine_id)
    if machine is None:
        return {
            "status": "not_found",
            "machine_id": machine_id,
            "message": f"No machine found for '{machine_id}'.",
        }

    notification = {
        "notification_id": f"NTF-{uuid4().hex[:8].upper()}",
        "machine_id": machine.machine_id,
        "technician": technician,
        "priority": priority.strip().upper(),
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "channel": "simulated",
    }
    store.add_notification(notification)

    return {
        "status": "success",
        "notification": notification,
    }
