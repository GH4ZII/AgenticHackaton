"""Machine domain model."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MachineStatus(str, Enum):
    HEALTHY = "HEALTHY"
    MONITORING = "MONITORING"
    WARNING = "WARNING"
    MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class Machine(BaseModel):
    machine_id: str
    name: str
    machine_type: str
    manufacturer: str
    model: str
    location: str
    status: MachineStatus = MachineStatus.HEALTHY
    temperature_limit: float = Field(description="Max normal temperature in C")
    vibration_limit: float = Field(description="Max normal vibration in mm/s")
    motor_current_limit: float = Field(description="Max normal motor current in A")
    notes: str | None = None
