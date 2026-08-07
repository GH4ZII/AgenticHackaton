"""Work order tools backed by the in-memory domain store."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.work_order import WorkOrder, WorkOrderStatus
from app.runtime import get_store


def create_work_order(
    machine_id: str,
    title: str,
    description: str,
    suspected_failure: str,
    priority: str,
    recommended_action: str,
    required_parts: list[str] | None = None,
    incident_id: str | None = None,
) -> dict:
    """Create a maintenance work order for a machine.

    Use this after diagnosing a fault when repair work should be scheduled.
    Prefer HIGH or URGENT priority for severe bearing or overheating issues.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".
        title: Short work order title.
        description: What needs to be done and why.
        suspected_failure: Likely failure mode.
        priority: Priority label such as LOW, MEDIUM, HIGH, or URGENT.
        recommended_action: Concrete repair action.
        required_parts: Optional list of part numbers or names.
        incident_id: Optional related incident id.

    Returns:
        Created work order payload, or an error if the machine is unknown.
    """
    store = get_store()
    machine = store.get_machine(machine_id)
    if machine is None:
        return {
            "status": "not_found",
            "machine_id": machine_id,
            "message": f"No machine found for '{machine_id}'.",
        }

    work_order = WorkOrder(
        work_order_id=f"WO-{uuid4().hex[:8].upper()}",
        machine_id=machine.machine_id,
        incident_id=incident_id,
        title=title,
        description=description,
        suspected_failure=suspected_failure,
        priority=priority.strip().upper() or "MEDIUM",
        recommended_action=recommended_action,
        required_parts=list(required_parts or []),
        status=WorkOrderStatus.OPEN,
        created_at=datetime.now(timezone.utc),
    )
    store.upsert_work_order(work_order)
    store.add_agent_action(
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "machine_id": machine.machine_id,
            "action": "work_order_created",
            "detail": f"Work order {work_order.work_order_id} created: {title}",
        }
    )

    return {
        "status": "success",
        "work_order": work_order.model_dump(mode="json"),
    }
