"""Telemetry domain model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TelemetrySample(BaseModel):
    machine_id: str
    timestamp: datetime
    temperature_c: float = Field(description="Temperature in Celsius")
    vibration_mm_s: float = Field(description="Vibration in mm/s")
    motor_current_a: float = Field(description="Motor current in Amperes")
