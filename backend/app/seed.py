"""Fake seed data for local development and Firestore bootstrap."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.inventory import InventoryItem
from app.models.machine import Machine, MachineStatus
from app.models.telemetry import TelemetrySample
from app.store.memory_store import MemoryStore


def _seed_into(store: Any) -> Any:
    """Write PUMP-04 demo data into any store with the domain API."""
    pump_04 = Machine(
        machine_id="PUMP-04",
        name="Cooling Water Pump 04",
        machine_type="centrifugal_pump",
        manufacturer="FlowTech Industrial",
        model="FT-C200",
        location="Plant A / Cooling Loop 2",
        status=MachineStatus.WARNING,
        temperature_limit=70.0,
        vibration_limit=4.5,
        motor_current_limit=12.5,
        notes="Drive-end bearing area flagged for elevated vibration.",
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

    store.set_maintenance_history(
        "PUMP-04",
        [
            {
                "date": "2026-02-12",
                "type": "inspection",
                "summary": "Routine vibration survey; drive-end bearing within limits.",
                "technician": "A. Berg",
            },
            {
                "date": "2025-11-03",
                "type": "component_replacement",
                "summary": "Replaced non-drive-end seal kit FT-C200-SEAL.",
                "technician": "M. Olsen",
            },
            {
                "date": "2025-06-18",
                "type": "fault",
                "summary": "Minor cavitation event; cleaned strainer and reset alarms.",
                "technician": "A. Berg",
            },
            {
                "date": "2026-07-01",
                "type": "inspection",
                "summary": "Last inspection noted early bearing noise under load.",
                "technician": "K. Nilsen",
            },
        ],
    )

    store.set_manual_sections(
        "PUMP-04",
        [
            {
                "section_id": "vib-limits",
                "title": "FT-C200 vibration limits",
                "tags": ["vibration", "bearing", "limits"],
                "content": (
                    "Normal overall vibration is 0.5–4.5 mm/s. Sustained readings "
                    "above 7.0 mm/s indicate probable drive-end bearing degradation. "
                    "Investigate immediately if temperature also rises."
                ),
            },
            {
                "section_id": "bearing-failure",
                "title": "Drive-end bearing failure symptoms",
                "tags": ["bearing", "failure", "temperature", "current"],
                "content": (
                    "Typical symptoms: rising vibration, rising bearing housing "
                    "temperature, and gradual motor current increase under constant "
                    "load. Recommended action: schedule bearing replacement "
                    "(part 6205-2RS) and notify on-call technician."
                ),
            },
            {
                "section_id": "safety",
                "title": "Safety and shutdown policy",
                "tags": ["safety", "shutdown", "critical"],
                "content": (
                    "Do not autonomously shut down the pump. For CRITICAL severity, "
                    "recommend shutdown and request human approval before any "
                    "isolation action."
                ),
            },
        ],
    )

    return store


def seed_store(store: MemoryStore | None = None) -> MemoryStore:
    """Populate an in-memory store with PUMP-04 demo data.

    Machine starts in WARNING because seed telemetry already shows
    bearing-degradation readings above normal limits.
    """
    if store is None:
        store = MemoryStore()
    else:
        store.clear()
    return _seed_into(store)


def seed_if_empty(store: Any) -> Any:
    """Seed demo data only when the store has no machines yet."""
    is_empty = getattr(store, "is_empty", None)
    if callable(is_empty):
        empty = is_empty()
    else:
        empty = store.get_machine("PUMP-04") is None
    if empty:
        return _seed_into(store)
    return store


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
