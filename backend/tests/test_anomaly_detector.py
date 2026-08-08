"""Anomaly detection tests (deterministic, no Gemini)."""

from __future__ import annotations

from app.models.incident import Severity
from app.models.machine import MachineStatus
from app.services.anomaly_detector import detect_anomaly
from tests.conftest import make_sample


def test_healthy_telemetry_no_incident(store):
    result = detect_anomaly(store, make_sample())
    assert result.is_anomalous is False
    assert result.created is False
    assert result.incident is None
    assert store.list_incidents() == []


def test_over_temperature_creates_incident_and_warning(store):
    # PUMP-04 temperature_limit = 70
    result = detect_anomaly(store, make_sample(temperature_c=86.0))
    assert result.is_anomalous is True
    assert result.created is True
    assert result.incident is not None
    assert result.incident.severity == Severity.MEDIUM
    assert "temperature" in result.incident.trigger_reason
    machine = store.get_machine("PUMP-04")
    assert machine is not None
    assert machine.status == MachineStatus.WARNING


def test_two_limits_yield_high_severity(store):
    result = detect_anomaly(
        store,
        make_sample(temperature_c=86.0, vibration_mm_s=8.0),
    )
    assert result.is_anomalous is True
    assert result.created is True
    assert result.incident is not None
    assert result.incident.severity == Severity.HIGH
    assert len(result.reasons) == 2


def test_three_limits_yield_high_severity(store):
    result = detect_anomaly(
        store,
        make_sample(temperature_c=86.0, vibration_mm_s=8.0, motor_current_a=14.0),
    )
    assert result.incident is not None
    assert result.incident.severity == Severity.HIGH
    assert len(result.reasons) == 3


def test_duplicate_open_incident_not_recreated(store):
    first = detect_anomaly(store, make_sample(temperature_c=86.0))
    assert first.created is True
    second = detect_anomaly(store, make_sample(temperature_c=90.0))
    assert second.is_anomalous is True
    assert second.created is False
    assert second.incident is not None
    assert first.incident is not None
    assert second.incident.incident_id == first.incident.incident_id
    assert len(store.list_incidents()) == 1
