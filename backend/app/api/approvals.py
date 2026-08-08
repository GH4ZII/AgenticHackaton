"""Human approval APIs for CRITICAL shutdown requests."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.serializers import approval_to_dict, machine_to_dict
from app.models.approval import ApprovalStatus
from app.models.machine import MachineStatus
from app.runtime import get_store

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("")
def list_approvals() -> dict:
    store = get_store()
    approvals = [approval_to_dict(a) for a in store.list_approvals()]
    approvals.sort(key=lambda a: a.get("created_at") or "", reverse=True)
    return {"approvals": approvals, "count": len(approvals)}


@router.get("/pending")
def list_pending_approvals() -> dict:
    store = get_store()
    pending = [
        approval_to_dict(a)
        for a in store.list_approvals()
        if a.status == ApprovalStatus.PENDING
    ]
    pending.sort(key=lambda a: a.get("created_at") or "", reverse=True)
    return {"approvals": pending, "count": len(pending)}


@router.post("/{approval_id}/approve")
def approve_shutdown(approval_id: str) -> dict:
    """Approve CRITICAL shutdown recommendation → set machine OUT_OF_SERVICE."""
    store = get_store()
    approval = store.get_approval(approval_id)
    if approval is None:
        raise HTTPException(
            status_code=404, detail=f"Approval '{approval_id}' not found"
        )
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Approval already {approval.status.value}",
        )

    now = datetime.now(timezone.utc)
    approval.status = ApprovalStatus.APPROVED
    approval.resolved_at = now
    approval.resolved_by = "operator"
    store.upsert_approval(approval)

    machine = store.get_machine(approval.machine_id)
    if machine is None:
        raise HTTPException(
            status_code=404,
            detail=f"Machine '{approval.machine_id}' not found",
        )
    machine.status = MachineStatus.OUT_OF_SERVICE
    store.upsert_machine(machine)

    store.add_agent_action(
        {
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "machine_id": approval.machine_id,
            "incident_id": approval.incident_id,
            "action": "shutdown_approved",
            "detail": (
                f"Human approved {approval.approval_id}. "
                f"Machine set to OUT_OF_SERVICE."
            ),
        }
    )

    return {
        "status": "ok",
        "message": "Shutdown approved. Machine set to OUT_OF_SERVICE.",
        "approval": approval_to_dict(approval),
        "machine": machine_to_dict(machine),
    }


@router.post("/{approval_id}/reject")
def reject_shutdown(approval_id: str) -> dict:
    """Reject CRITICAL shutdown — machine stays MAINTENANCE_REQUIRED."""
    store = get_store()
    approval = store.get_approval(approval_id)
    if approval is None:
        raise HTTPException(
            status_code=404, detail=f"Approval '{approval_id}' not found"
        )
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Approval already {approval.status.value}",
        )

    now = datetime.now(timezone.utc)
    approval.status = ApprovalStatus.REJECTED
    approval.resolved_at = now
    approval.resolved_by = "operator"
    store.upsert_approval(approval)

    machine = store.get_machine(approval.machine_id)
    if machine is not None and machine.status != MachineStatus.OUT_OF_SERVICE:
        # Keep maintenance posture; do not escalate to shutdown.
        if machine.status != MachineStatus.MAINTENANCE_REQUIRED:
            machine.status = MachineStatus.MAINTENANCE_REQUIRED
            store.upsert_machine(machine)

    store.add_agent_action(
        {
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "machine_id": approval.machine_id,
            "incident_id": approval.incident_id,
            "action": "shutdown_rejected",
            "detail": (
                f"Human rejected {approval.approval_id}. "
                "Machine remains MAINTENANCE_REQUIRED. Shutdown NOT executed."
            ),
        }
    )

    return {
        "status": "ok",
        "message": "Shutdown rejected. Machine remains in maintenance.",
        "approval": approval_to_dict(approval),
        "machine": machine_to_dict(machine) if machine else None,
    }
