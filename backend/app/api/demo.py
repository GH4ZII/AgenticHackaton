"""Demo seed endpoint for UI without calling Gemini."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.incident import Incident, IncidentStatus, Severity
from app.models.machine import MachineStatus
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.runtime import get_store
from app.seed import seed_if_empty

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/seed")
def seed_demo_state() -> dict:
    """Ensure PUMP-04 demo data exists for the dashboard (no Gemini).

    Creates a representative open incident, work order, and agent_actions
    if they are missing — so judges can explore the UI immediately.
    """
    store = get_store()
    seed_if_empty(store)

    machine = store.get_machine("PUMP-04")
    if machine is None:
        return {"status": "error", "message": "PUMP-04 missing after seed"}

    machine.status = MachineStatus.MAINTENANCE_REQUIRED
    store.upsert_machine(machine)

    open_incident = store.get_open_incident_for_machine("PUMP-04")
    now = datetime.now(timezone.utc)

    if open_incident is None:
        open_incident = Incident(
            incident_id="INC-DEMO01",
            machine_id="PUMP-04",
            status=IncidentStatus.INVESTIGATING,
            severity=Severity.HIGH,
            suspected_failure="Drive-end bearing degradation",
            confidence=0.93,
            detected_at=now,
            trigger_reason=(
                "temperature 86.0 C exceeds limit 70.0 C; "
                "vibration 8.7 mm/s exceeds limit 4.5 mm/s; "
                "motor current 14.0 A exceeds limit 12.5 A"
            ),
            agent_summary=(
                "Likely drive-end bearing degradation. Vibration, temperature, "
                "and motor current are all above limits and rising. "
                "Part 6205-2RS is in stock. Work order created and technician notified."
            ),
        )
        store.add_incident(open_incident)
        created_incident = True
    else:
        if not open_incident.agent_summary:
            open_incident.agent_summary = (
                "Likely drive-end bearing degradation based on telemetry and manual."
            )
            open_incident.suspected_failure = (
                open_incident.suspected_failure or "Drive-end bearing degradation"
            )
            open_incident.confidence = open_incident.confidence or 0.9
            open_incident.status = IncidentStatus.INVESTIGATING
            store.add_incident(open_incident)
        created_incident = False

    related = [
        w
        for w in store.list_work_orders()
        if w.machine_id == "PUMP-04" and w.status != WorkOrderStatus.COMPLETED
    ]
    if not related:
        wo = WorkOrder(
            work_order_id="WO-DEMO01",
            machine_id="PUMP-04",
            incident_id=open_incident.incident_id,
            title="Replace drive-end ball bearing",
            description=(
                "Replace drive-end bearing 6205-2RS due to elevated vibration "
                "and temperature on PUMP-04."
            ),
            suspected_failure="Drive-end bearing degradation",
            priority="HIGH",
            recommended_action="Replace bearing and re-check vibration under load.",
            required_parts=["6205-2RS"],
            status=WorkOrderStatus.OPEN,
            created_at=now,
        )
        store.upsert_work_order(wo)
        created_wo = True
    else:
        created_wo = False

    existing_actions = store.list_agent_actions()
    if len(existing_actions) < 3:
        for action, detail in [
            (
                "anomaly_detected",
                "Telemetry exceeded limits on PUMP-04",
            ),
            (
                "investigation_started",
                f"Auto-started investigation for {open_incident.incident_id}",
            ),
            (
                "work_order_created",
                "Work order created for bearing replacement",
            ),
            (
                "technician_notified",
                "On-call technician notified (HIGH)",
            ),
            (
                "machine_status_updated",
                "Machine status set to MAINTENANCE_REQUIRED",
            ),
            (
                "investigation_finished",
                "Agent completed diagnosis with HIGH severity",
            ),
        ]:
            store.add_agent_action(
                {
                    "timestamp": now.isoformat().replace("+00:00", "Z"),
                    "machine_id": "PUMP-04",
                    "incident_id": open_incident.incident_id,
                    "action": action,
                    "detail": detail,
                }
            )

    return {
        "status": "ok",
        "machine_id": "PUMP-04",
        "incident_id": open_incident.incident_id,
        "created_incident": created_incident,
        "created_work_order": created_wo,
        "incident_count": len(store.list_incidents()),
        "work_order_count": len(store.list_work_orders()),
        "agent_action_count": len(store.list_agent_actions()),
    }
