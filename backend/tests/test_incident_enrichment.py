"""Tests for incident diagnosis enrichment."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.incident import Incident, IncidentStatus, Severity
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.services.incident_enrichment import enrich_incident_diagnosis


def test_enrich_from_work_order_and_summary(store):
    incident = Incident(
        incident_id="INC-ENR1",
        machine_id="FAN-01",
        status=IncidentStatus.INVESTIGATING,
        severity=Severity.MEDIUM,
        detected_at=datetime.now(timezone.utc),
        trigger_reason="vibration high",
        agent_summary=(
            "#### 1. Likely Failure Mode\n"
            "Drive-End Bearing Wear\n\n"
            "#### 3. Confidence\n"
            "Confidence: 82%\n"
        ),
    )
    store.add_incident(incident)
    store.upsert_work_order(
        WorkOrder(
            work_order_id="WO-ENR1",
            machine_id="FAN-01",
            incident_id="INC-ENR1",
            title="Replace bearing",
            description="Replace bearing",
            suspected_failure="Drive-end bearing wear",
            priority="MEDIUM",
            recommended_action="Replace PART-6205-2RS",
            required_parts=["6205-2RS"],
            status=WorkOrderStatus.OPEN,
            created_at=datetime.now(timezone.utc),
        )
    )

    enriched = enrich_incident_diagnosis(store, incident)
    assert enriched.suspected_failure == "Drive-end bearing wear"
    assert enriched.confidence == 0.82


def test_enrich_parses_failure_when_no_work_order(store):
    incident = Incident(
        incident_id="INC-ENR2",
        machine_id="CNC-02",
        status=IncidentStatus.INVESTIGATING,
        severity=Severity.HIGH,
        detected_at=datetime.now(timezone.utc),
        trigger_reason="temp high",
        agent_summary="Likely failure mode: Spindle overheating under load\nConfidence: 91%",
    )
    store.add_incident(incident)

    enriched = enrich_incident_diagnosis(store, incident)
    assert enriched.suspected_failure is not None
    assert "Spindle overheating" in enriched.suspected_failure
    assert enriched.confidence == 0.91


def test_sanitize_latex_and_parse_reasoning(store):
    from app.services.incident_enrichment import parse_reasoning, sanitize_agent_text

    raw = (
        "Confidence: 95%\n"
        "Reasoning: temperature: $60.54\\circ\\text{C}$ vs. $60.0\\circ\\text{C}$ max "
        "and vibration: $2.64\\text{ mm/s}$ vs. $3.0\\text{ mm/s}$ max.\n\n"
        "5. Actions Taken\n"
        "- Work order created"
    )
    cleaned = sanitize_agent_text(raw)
    assert "$" not in cleaned
    assert "^°" not in cleaned
    assert "°" in cleaned or "C" in cleaned
    assert r"\text" not in cleaned

    incident = Incident(
        incident_id="INC-ENR3",
        machine_id="CONV-03",
        status=IncidentStatus.INVESTIGATING,
        severity=Severity.HIGH,
        detected_at=datetime.now(timezone.utc),
        trigger_reason="temp",
        agent_summary=raw,
    )
    store.add_incident(incident)
    enriched = enrich_incident_diagnosis(store, incident)
    assert enriched.confidence == 0.95
    assert "$" not in (enriched.agent_summary or "")
    reasoning = parse_reasoning(enriched.agent_summary or "")
    assert reasoning is not None
    assert "temperature" in reasoning.lower()
