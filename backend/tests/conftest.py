"""Shared fixtures for Phase 11 domain tests (MemoryStore, no Firestore/Gemini)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.telemetry import TelemetrySample
from app.seed import seed_store


@pytest.fixture
def store(monkeypatch):
    """Seeded in-memory store bound to app.runtime.STORE."""
    monkeypatch.setenv("USE_FIRESTORE", "false")
    domain = seed_store()
    monkeypatch.setattr("app.runtime.STORE", domain)
    return domain


def make_sample(
    *,
    machine_id: str = "PUMP-04",
    temperature_c: float = 62.0,
    vibration_mm_s: float = 3.0,
    motor_current_a: float = 11.0,
    timestamp: datetime | None = None,
) -> TelemetrySample:
    """Build a TelemetrySample with defaults under PUMP-04 limits."""
    return TelemetrySample(
        machine_id=machine_id,
        timestamp=timestamp or datetime.now(timezone.utc),
        temperature_c=temperature_c,
        vibration_mm_s=vibration_mm_s,
        motor_current_a=motor_current_a,
    )
