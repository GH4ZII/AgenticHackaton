"""Human approval API tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.approval import ApprovalRequest, ApprovalStatus
from app.models.incident import Incident, IncidentStatus, Severity
from app.models.machine import MachineStatus
from app.seed import seed_store


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("USE_FIRESTORE", "false")
    domain = seed_store()
    monkeypatch.setattr("app.runtime.STORE", domain)

    # Seed a pending CRITICAL approval + maintenance posture.
    incident = Incident(
        incident_id="INC-APR1",
        machine_id="PUMP-04",
        status=IncidentStatus.INVESTIGATING,
        severity=Severity.CRITICAL,
        detected_at=datetime.now(timezone.utc),
        trigger_reason="critical overheat",
    )
    domain.add_incident(incident)
    approval = ApprovalRequest(
        approval_id="APR-TEST01",
        incident_id="INC-APR1",
        machine_id="PUMP-04",
        reason="Recommend shutdown",
        status=ApprovalStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )
    domain.upsert_approval(approval)
    machine = domain.get_machine("PUMP-04")
    assert machine is not None
    machine.status = MachineStatus.MAINTENANCE_REQUIRED
    domain.upsert_machine(machine)

    with TestClient(app) as test_client:
        yield test_client, domain


def test_list_pending_approvals(client):
    test_client, _ = client
    response = test_client.get("/api/approvals/pending")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    assert any(a["approval_id"] == "APR-TEST01" for a in body["approvals"])


def test_approve_sets_out_of_service(client):
    test_client, domain = client
    response = test_client.post("/api/approvals/APR-TEST01/approve")
    assert response.status_code == 200
    body = response.json()
    assert body["approval"]["status"] == "APPROVED"
    assert domain.get_machine("PUMP-04").status == MachineStatus.OUT_OF_SERVICE
    assert any(
        a["action"] == "shutdown_approved" for a in domain.list_agent_actions()
    )


def test_reject_keeps_maintenance_required(client):
    test_client, domain = client
    response = test_client.post("/api/approvals/APR-TEST01/reject")
    assert response.status_code == 200
    body = response.json()
    assert body["approval"]["status"] == "REJECTED"
    assert domain.get_machine("PUMP-04").status == MachineStatus.MAINTENANCE_REQUIRED
    assert domain.get_machine("PUMP-04").status != MachineStatus.OUT_OF_SERVICE


def test_approve_twice_conflicts(client):
    test_client, _ = client
    assert test_client.post("/api/approvals/APR-TEST01/approve").status_code == 200
    second = test_client.post("/api/approvals/APR-TEST01/approve")
    assert second.status_code == 409


def test_approve_missing_404(client):
    test_client, _ = client
    response = test_client.post("/api/approvals/APR-MISSING/approve")
    assert response.status_code == 404
