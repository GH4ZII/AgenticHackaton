"""Fake seed data for Phase 2 local development."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.inventory import InventoryItem
from app.models.machine import Machine, MachineStatus
from app.models.telemetry import TelemetrySample
from app.store.memory_store import MemoryStore


def seed_store(store: MemoryStore | None = None) -> MemoryStore:
    """Populate an in-memory store with PUMP-04 demo data.

    Machine starts HEALTHY; seed telemetry includes the bearing-degradation
    trend used in the hackathon demo scenario.
    """
    if store is None:
        store = MemoryStore()
    else:
        store.clear()

    pump_04 = Machine(
        machine_id="PUMP-04",
        name="Cooling Water Pump 04",
        machine_type="centrifugal_pump",
        manufacturer="FlowTech Industrial",
        model="FT-C200",
        location="Plant A / Cooling Loop 2",
        status=MachineStatus.HEALTHY,
        temperature_limit=70.0,
        vibration_limit=4.5,
        motor_current_limit=12.5,
        notes="Drive-end bearing is a known wear point on FT-C200 units.",
    )
    store.upsert_machine(pump_04)

    telemetry_rows = [
        ("2026-08-07T08:00:00Z", 62.0, 3.1, 11.0),
        ("2026-08-07T09:00:00Z", 66.0, 3.8, 11.5),
        ("2026-08-07T10:00:00Z", 71.0, 5.4, 12.8),
        ("2026-08-07T11:00:00Z", 78.0, 7.2, 13.5),
        ("2026-08-07T12:00:00Z", 86.0, 8.7, 14.0),
    ]
    for ts, temp, vib, current in telemetry_rows:
        store.add_telemetry(
            TelemetrySample(
                machine_id="PUMP-04",
                timestamp=datetime.fromisoformat(ts.replace("Z", "+00:00")),
                temperature_c=temp,
                vibration_mm_s=vib,
                motor_current_a=current,
            )
        )

    store.upsert_inventory_item(
        InventoryItem(
            part_id="PART-6205-2RS",
            name="Drive-end ball bearing",
            part_number="6205-2RS",
            stock=3,
            location="Warehouse A / Shelf B-12",
        )
    )
    store.upsert_inventory_item(
        InventoryItem(
            part_id="PART-SEAL-FT200",
            name="Pump shaft seal kit",
            part_number="FT-C200-SEAL",
            stock=2,
            location="Warehouse A / Shelf B-14",
        )
    )

    return store


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
