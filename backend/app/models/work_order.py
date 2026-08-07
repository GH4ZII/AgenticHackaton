"""Work order domain model."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorkOrderStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkOrder(BaseModel):
    work_order_id: str
    machine_id: str
    incident_id: str | None = None
    title: str
    description: str
    suspected_failure: str | None = None
    priority: str = "MEDIUM"
    recommended_action: str | None = None
    required_parts: list[str] = Field(default_factory=list)
    status: WorkOrderStatus = WorkOrderStatus.OPEN
    created_at: datetime
    completed_at: datetime | None = None
