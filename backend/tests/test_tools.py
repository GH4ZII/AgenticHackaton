"""Agent tool behavior tests against MemoryStore."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.approval import ApprovalStatus
from app.models.incident import Incident, IncidentStatus, Severity
from app.models.machine import MachineStatus
from app.models.work_order import WorkOrderStatus
from maintenance_agent.tools.approval_tools import request_shutdown_approval
from maintenance_agent.tools.incident_tools import resolve_incident
from maintenance_agent.tools.inventory_tools import check_inventory
from maintenance_agent.tools.machine_tools import (
    get_machine_context,
    update_machine_status,
)
from maintenance_agent.tools.work_order_tools import create_work_order


def test_get_machine_context_success(store):
    result = get_machine_context("PUMP-04")
    assert result["status"] == "success"
    assert result["machine"]["machine_id"] == "PUMP-04"
    assert "normal_operating_limits" in result["machine"]


def test_get_machine_context_not_found(store):
    result = get_machine_context("UNKNOWN")
    assert result["status"] == "not_found"


def test_update_machine_status(store):
    result = update_machine_status("PUMP-04", "MAINTENANCE_REQUIRED")
    assert result["status"] == "success"
    assert result["new_status"] == "MAINTENANCE_REQUIRED"
    assert store.get_machine("PUMP-04").status == MachineStatus.MAINTENANCE_REQUIRED


def test_update_machine_status_invalid(store):
    result = update_machine_status("PUMP-04", "BROKEN")
    assert result["status"] == "error"


def test_check_inventory_finds_bearing(store):
    result = check_inventory("bearing")
    assert result["status"] == "success"
    assert result["match_count"] >= 1
    assert any("bearing" in m["name"].lower() for m in result["matches"])


def test_create_work_order_persists(store):
    result = create_work_order(
        machine_id="PUMP-04",
        title="Replace drive-end bearing",
        description="Elevated vibration and temperature",
        suspected_failure="Drive-end bearing degradation",
        priority="HIGH",
        recommended_action="Replace 6205-2RS",
        required_parts=["6205-2RS"],
        incident_id="INC-TEST01",
    )
    assert result["status"] == "success"
    wo_id = result["work_order"]["work_order_id"]
    stored = store.get_work_order(wo_id)
    assert stored is not None
    assert stored.status == WorkOrderStatus.OPEN
    assert stored.priority == "HIGH"
    assert any(a["action"] == "work_order_created" for a in store.list_agent_actions())


def test_create_work_order_unknown_machine(store):
    result = create_work_order(
        machine_id="NOPE",
        title="x",
        description="y",
        suspected_failure="z",
        priority="LOW",
        recommended_action="n/a",
    )
    assert result["status"] == "not_found"


def test_resolve_incident(store):
    incident = Incident(
        incident_id="INC-RESOLVE1",
        machine_id="PUMP-04",
        status=IncidentStatus.INVESTIGATING,
        severity=Severity.HIGH,
        detected_at=datetime.now(timezone.utc),
        trigger_reason="test",
    )
    store.add_incident(incident)

    result = resolve_incident("INC-RESOLVE1", summary="Telemetry within limits")
    assert result["status"] == "success"
    updated = store.incidents["INC-RESOLVE1"]
    assert updated.status == IncidentStatus.RESOLVED
    assert updated.resolved_at is not None


def test_request_shutdown_approval_does_not_shut_down(store):
    incident = Incident(
        incident_id="INC-CRIT1",
        machine_id="PUMP-04",
        status=IncidentStatus.OPEN,
        severity=Severity.CRITICAL,
        detected_at=datetime.now(timezone.utc),
        trigger_reason="critical overheat",
    )
    store.add_incident(incident)
    before = store.get_machine("PUMP-04").status

    result = request_shutdown_approval(
        machine_id="PUMP-04",
        incident_id="INC-CRIT1",
        reason="Imminent bearing seizure risk",
    )
    assert result["status"] == "success"
    assert result["shutdown_executed"] is False
    assert result["approval"]["status"] == ApprovalStatus.PENDING.value
    assert store.get_machine("PUMP-04").status == before
    assert store.get_machine("PUMP-04").status != MachineStatus.OUT_OF_SERVICE


def test_request_shutdown_approval_reuses_pending(store):
    incident = Incident(
        incident_id="INC-CRIT2",
        machine_id="PUMP-04",
        status=IncidentStatus.OPEN,
        severity=Severity.CRITICAL,
        detected_at=datetime.now(timezone.utc),
        trigger_reason="critical",
    )
    store.add_incident(incident)
    first = request_shutdown_approval("PUMP-04", "INC-CRIT2", "reason A")
    second = request_shutdown_approval("PUMP-04", "INC-CRIT2", "reason B")
    assert first["approval"]["approval_id"] == second["approval"]["approval_id"]
    assert len(store.list_approvals()) == 1
