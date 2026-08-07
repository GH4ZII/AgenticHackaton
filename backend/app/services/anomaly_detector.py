"""Deterministic anomaly detection (no Gemini / no ML)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.store.protocol import DomainStore
from app.models.incident import Incident, IncidentStatus, Severity
from app.models.machine import Machine, MachineStatus
from app.models.telemetry import TelemetrySample


@dataclass
class AnomalyResult:
    is_anomalous: bool
    reasons: list[str]
    incident: Incident | None = None


def _exceeded_limits(sample: TelemetrySample, machine: Machine) -> list[str]:
    reasons: list[str] = []
    if sample.temperature_c > machine.temperature_limit:
        reasons.append(
            f"temperature {sample.temperature_c} C exceeds limit "
            f"{machine.temperature_limit} C"
        )
    if sample.vibration_mm_s > machine.vibration_limit:
        reasons.append(
            f"vibration {sample.vibration_mm_s} mm/s exceeds limit "
            f"{machine.vibration_limit} mm/s"
        )
    if sample.motor_current_a > machine.motor_current_limit:
        reasons.append(
            f"motor current {sample.motor_current_a} A exceeds limit "
            f"{machine.motor_current_limit} A"
        )
    return reasons


def _estimate_severity(reasons: list[str]) -> Severity:
    if len(reasons) >= 3:
        return Severity.HIGH
    if len(reasons) == 2:
        return Severity.HIGH
    return Severity.MEDIUM


def detect_anomaly(
    store: DomainStore,
    sample: TelemetrySample,
    *,
    persist_sample: bool = True,
) -> AnomalyResult:
    """Check telemetry against machine limits and create an incident if needed.

    If an open incident already exists for the machine, return it instead of
    creating a duplicate.
    """
    machine = store.get_machine(sample.machine_id)
    if machine is None:
        raise ValueError(f"Unknown machine_id: {sample.machine_id}")

    if persist_sample:
        store.add_telemetry(sample)

    reasons = _exceeded_limits(sample, machine)
    if not reasons:
        return AnomalyResult(is_anomalous=False, reasons=[])

    existing = store.get_open_incident_for_machine(machine.machine_id)
    if existing is not None:
        return AnomalyResult(
            is_anomalous=True,
            reasons=reasons,
            incident=existing,
        )

    incident = Incident(
        incident_id=f"INC-{uuid4().hex[:8].upper()}",
        machine_id=machine.machine_id,
        status=IncidentStatus.OPEN,
        severity=_estimate_severity(reasons),
        suspected_failure=None,
        detected_at=sample.timestamp
        if sample.timestamp.tzinfo
        else sample.timestamp.replace(tzinfo=timezone.utc),
        trigger_reason="; ".join(reasons),
    )
    store.add_incident(incident)

    machine.status = MachineStatus.WARNING
    store.upsert_machine(machine)

    return AnomalyResult(is_anomalous=True, reasons=reasons, incident=incident)


def evaluate_latest_for_machine(store: DomainStore, machine_id: str) -> AnomalyResult:
    """Run detection on the most recent stored telemetry sample for a machine."""
    samples = store.get_telemetry_for_machine(machine_id)
    if not samples:
        raise ValueError(f"No telemetry found for machine_id: {machine_id}")

    latest = max(samples, key=lambda s: s.timestamp)
    return detect_anomaly(store, latest, persist_sample=False)
