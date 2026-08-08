"""Repair / closed-loop workflow tests (verification agent mocked)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.incident import Incident, IncidentStatus, Severity
from app.models.machine import MachineStatus
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.services.agent_runner import AgentRunResult
from app.services.repair_workflow import complete_and_verify


def _seed_open_repair(store) -> tuple[str, str]:
    incident = Incident(
        incident_id="INC-REPAIR1",
        machine_id="PUMP-04",
        status=IncidentStatus.INVESTIGATING,
        severity=Severity.HIGH,
        detected_at=datetime.now(timezone.utc),
        trigger_reason="bearing degradation",
    )
    store.add_incident(incident)
    wo = WorkOrder(
        work_order_id="WO-REPAIR1",
        machine_id="PUMP-04",
        incident_id="INC-REPAIR1",
        title="Replace bearing",
        description="Drive-end bearing",
        priority="HIGH",
        status=WorkOrderStatus.OPEN,
        created_at=datetime.now(timezone.utc),
    )
    store.upsert_work_order(wo)
    machine = store.get_machine("PUMP-04")
    assert machine is not None
    machine.status = MachineStatus.MAINTENANCE_REQUIRED
    store.upsert_machine(machine)
    return wo.work_order_id, incident.incident_id


@pytest.mark.asyncio
async def test_complete_and_verify_marks_completed_and_resolves(store):
    wo_id, incident_id = _seed_open_repair(store)
    mock_result = AgentRunResult(
        prompt="verify",
        tool_calls=[],
        final_text="Looks healthy.",
    )

    with patch(
        "app.services.repair_workflow.run_verification_agent",
        new=AsyncMock(return_value=mock_result),
    ) as mock_agent:
        result = await complete_and_verify(store, wo_id)

    mock_agent.assert_awaited_once()
    assert result.already_completed is False
    assert result.agent_invoked is True
    assert result.work_order.status == WorkOrderStatus.COMPLETED
    assert result.work_order.completed_at is not None

    incident = store.incidents[incident_id]
    assert incident.status == IncidentStatus.RESOLVED
    machine = store.get_machine("PUMP-04")
    assert machine is not None
    assert machine.status == MachineStatus.HEALTHY
    assert len(store.get_telemetry_for_machine("PUMP-04")) >= 3


@pytest.mark.asyncio
async def test_complete_already_completed_is_idempotent(store):
    wo_id, _ = _seed_open_repair(store)
    with patch(
        "app.services.repair_workflow.run_verification_agent",
        new=AsyncMock(
            return_value=AgentRunResult(prompt="v", tool_calls=[], final_text="ok")
        ),
    ):
        await complete_and_verify(store, wo_id)

    second = await complete_and_verify(store, wo_id)
    assert second.already_completed is True
    assert second.agent_invoked is False


@pytest.mark.asyncio
async def test_complete_unknown_work_order(store):
    with pytest.raises(ValueError, match="not found"):
        await complete_and_verify(store, "WO-MISSING")
