"""Incident domain model."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Incident(BaseModel):
    incident_id: str
    machine_id: str
    status: IncidentStatus = IncidentStatus.OPEN
    severity: Severity = Severity.MEDIUM
    suspected_failure: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    detected_at: datetime
    resolved_at: datetime | None = None
    trigger_reason: str
    agent_summary: str | None = None
