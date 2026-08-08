"""Human approval requests for safety-critical actions."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRequest(BaseModel):
    approval_id: str
    incident_id: str
    machine_id: str
    reason: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None
