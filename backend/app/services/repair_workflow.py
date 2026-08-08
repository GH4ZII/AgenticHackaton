"""Closed-loop repair completion and verification (Phase 8)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.models.incident import Incident, IncidentStatus
from app.models.machine import MachineStatus
from app.models.telemetry import TelemetrySample
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.services.agent_runner import AgentRunResult, run_verification_agent
from app.store.protocol import DomainStore


@dataclass
class RepairWorkflowResult:
    work_order: WorkOrder
    incident: Incident | None
    machine_status: str | None
    already_completed: bool
    agent_invoked: bool
    agent_result: AgentRunResult | None = None
    message: str = ""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _find_incident(store: DomainStore, work_order: WorkOrder) -> Incident | None:
    if work_order.incident_id:
        for incident in store.list_incidents():
            if incident.incident_id == work_order.incident_id:
                return incident
        if hasattr(store, "get_incident"):
            found = store.get_incident(work_order.incident_id)
            if found is not None:
                return found
    return store.get_open_incident_for_machine(work_order.machine_id)


def _inject_healthy_telemetry(store: DomainStore, machine_id: str) -> None:
    base = _now()
    healthy_rows = [
        (0, 61.5, 2.9, 10.8),
        (5, 62.0, 3.0, 11.0),
        (10, 61.8, 3.1, 10.9),
    ]
    for minutes, temp, vib, current in healthy_rows:
        store.add_telemetry(
            TelemetrySample(
                machine_id=machine_id,
                timestamp=base + timedelta(minutes=minutes),
                temperature_c=temp,
                vibration_mm_s=vib,
                motor_current_a=current,
            )
        )


async def complete_and_verify(
    store: DomainStore,
    work_order_id: str,
    *,
    invoke_agent: bool = True,
) -> RepairWorkflowResult:
    """Mark work order completed, inject healthy telemetry, verify with agent."""
    work_order = store.get_work_order(work_order_id)
    if work_order is None:
        raise ValueError(f"Work order '{work_order_id}' not found")

    if work_order.status == WorkOrderStatus.COMPLETED:
        incident = _find_incident(store, work_order)
        machine = store.get_machine(work_order.machine_id)
        return RepairWorkflowResult(
            work_order=work_order,
            incident=incident,
            machine_status=machine.status.value if machine else None,
            already_completed=True,
            agent_invoked=False,
            message="Work order was already completed.",
        )

    now = _now()
    work_order.status = WorkOrderStatus.COMPLETED
    work_order.completed_at = now
    store.upsert_work_order(work_order)
    store.add_agent_action(
        {
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "machine_id": work_order.machine_id,
            "incident_id": work_order.incident_id,
            "action": "work_order_completed",
            "detail": f"Work order {work_order.work_order_id} marked COMPLETED.",
        }
    )

    _inject_healthy_telemetry(store, work_order.machine_id)

    machine = store.get_machine(work_order.machine_id)
    if machine is not None:
        machine.status = MachineStatus.MONITORING
        store.upsert_machine(machine)

    incident = _find_incident(store, work_order)
    if incident is None:
        return RepairWorkflowResult(
            work_order=work_order,
            incident=None,
            machine_status=machine.status.value if machine else None,
            already_completed=False,
            agent_invoked=False,
            message="Work order completed; no linked incident to verify.",
        )

    if not invoke_agent:
        return RepairWorkflowResult(
            work_order=work_order,
            incident=incident,
            machine_status=machine.status.value if machine else None,
            already_completed=False,
            agent_invoked=False,
            message="Work order completed; agent verification skipped.",
        )

    store.add_agent_action(
        {
            "timestamp": _now().isoformat().replace("+00:00", "Z"),
            "machine_id": work_order.machine_id,
            "incident_id": incident.incident_id,
            "action": "verification_started",
            "detail": f"Verifying repair for {work_order.work_order_id}",
        }
    )

    agent_result = await run_verification_agent(
        work_order.machine_id,
        incident,
        work_order.work_order_id,
    )

    # Refresh incident/machine after agent tools may have updated them.
    refreshed = _find_incident(store, work_order)
    if refreshed is not None:
        incident = refreshed
    machine = store.get_machine(work_order.machine_id)

    # Deterministic safety net if agent forgot tools but telemetry is healthy.
    if (
        incident.status != IncidentStatus.RESOLVED
        and machine is not None
    ):
        samples = store.get_telemetry_for_machine(machine.machine_id)
        if samples:
            latest = max(samples, key=lambda s: s.timestamp)
            healthy = (
                latest.temperature_c <= machine.temperature_limit
                and latest.vibration_mm_s <= machine.vibration_limit
                and latest.motor_current_a <= machine.motor_current_limit
            )
            if healthy:
                from maintenance_agent.tools.incident_tools import resolve_incident
                from maintenance_agent.tools.machine_tools import update_machine_status

                resolve_incident(
                    incident.incident_id,
                    summary="Auto-resolved: post-repair telemetry within limits.",
                )
                update_machine_status(machine.machine_id, "HEALTHY")
                incident = _find_incident(store, work_order) or incident
                machine = store.get_machine(work_order.machine_id)

    store.add_agent_action(
        {
            "timestamp": _now().isoformat().replace("+00:00", "Z"),
            "machine_id": work_order.machine_id,
            "incident_id": incident.incident_id if incident else None,
            "action": "verification_finished",
            "detail": (
                f"Tools: {', '.join(agent_result.tool_calls) or 'none'}. "
                f"Incident status: "
                f"{incident.status.value if incident else 'n/a'}."
            ),
        }
    )

    return RepairWorkflowResult(
        work_order=work_order,
        incident=incident,
        machine_status=machine.status.value if machine else None,
        already_completed=False,
        agent_invoked=True,
        agent_result=agent_result,
        message="Work order completed and repair verification finished.",
    )


def complete_and_verify_sync(store: DomainStore, work_order_id: str, **kwargs: Any):
    import asyncio

    return asyncio.run(complete_and_verify(store, work_order_id, **kwargs))
