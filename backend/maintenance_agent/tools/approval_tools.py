"""Safety tools: human approval for shutdown (never auto-shutdown)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.approval import ApprovalRequest, ApprovalStatus
from app.runtime import get_store


def request_shutdown_approval(
    machine_id: str,
    incident_id: str,
    reason: str,
) -> dict:
    """Request human approval for a recommended machine shutdown.

    Use ONLY for CRITICAL severity. Creates a PENDING approval request.
    Does NOT shut down the machine. A human must approve or reject in the UI.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".
        incident_id: Related incident id.
        reason: Why shutdown is recommended.

    Returns:
        Approval request payload. shutdown_executed is always false.
    """
    store = get_store()
    machine = store.get_machine(machine_id)
    if machine is None:
        return {
            "status": "not_found",
            "machine_id": machine_id,
            "message": f"No machine found for '{machine_id}'.",
            "shutdown_executed": False,
        }

    # Reuse existing pending approval for this incident if present.
    for existing in store.list_approvals():
        if (
            existing.incident_id == incident_id
            and existing.status == ApprovalStatus.PENDING
        ):
            return {
                "status": "success",
                "approval": existing.model_dump(mode="json"),
                "shutdown_executed": False,
                "message": (
                    "Pending shutdown approval already exists. "
                    "Awaiting human Approve/Reject. Machine was NOT shut down."
                ),
            }

    now = datetime.now(timezone.utc)
    approval = ApprovalRequest(
        approval_id=f"APR-{uuid4().hex[:8].upper()}",
        incident_id=incident_id,
        machine_id=machine.machine_id,
        reason=reason,
        status=ApprovalStatus.PENDING,
        created_at=now,
    )
    store.upsert_approval(approval)
    store.add_agent_action(
        {
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "machine_id": machine.machine_id,
            "incident_id": incident_id,
            "action": "shutdown_approval_requested",
            "detail": (
                f"CRITICAL shutdown recommended. Approval {approval.approval_id} "
                "PENDING. Machine was NOT shut down."
            ),
        }
    )

    return {
        "status": "success",
        "approval": approval.model_dump(mode="json"),
        "shutdown_executed": False,
        "message": (
            "Shutdown approval requested. Waiting for human decision. "
            "Machine was NOT shut down."
        ),
    }
