"""Fake seed data for local development and Firestore bootstrap."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.inventory import InventoryItem
from app.models.machine import Machine, MachineStatus
from app.models.telemetry import TelemetrySample
from app.store.memory_store import MemoryStore


def _add_telemetry(
    store: Any,
    machine_id: str,
    rows: list[tuple[str, float, float, float]],
) -> None:
    for ts, temp, vib, current in rows:
        store.add_telemetry(
            TelemetrySample(
                machine_id=machine_id,
                timestamp=datetime.fromisoformat(ts.replace("Z", "+00:00")),
                temperature_c=temp,
                vibration_mm_s=vib,
                motor_current_a=current,
            )
        )


def _seed_into(store: Any) -> Any:
    """Write fleet + PUMP-04 demo data into any store with the domain API."""
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
        notes="Drive-end bearing monitored; use simulator for live degradation.",
    )
    store.upsert_machine(pump_04)

    cnc_02 = Machine(
        machine_id="CNC-02",
        name="CNC Milling Center 02",
        machine_type="cnc_mill",
        manufacturer="Nordic Machining",
        model="NM-4500",
        location="Plant A / Machining Bay 1",
        status=MachineStatus.HEALTHY,
        temperature_limit=65.0,
        vibration_limit=3.5,
        motor_current_limit=18.0,
        notes="Spindle and axis drives within normal operating band.",
    )
    store.upsert_machine(cnc_02)

    fan_01 = Machine(
        machine_id="FAN-01",
        name="HVAC Exhaust Fan 01",
        machine_type="industrial_fan",
        manufacturer="AirCore Systems",
        model="AC-EX90",
        location="Plant A / Roof Vent Zone B",
        status=MachineStatus.HEALTHY,
        temperature_limit=55.0,
        vibration_limit=4.0,
        motor_current_limit=9.5,
        notes="Belt-driven exhaust fan; last balance check passed.",
    )
    store.upsert_machine(fan_01)

    conv_03 = Machine(
        machine_id="CONV-03",
        name="Parts Conveyor 03",
        machine_type="conveyor",
        manufacturer="LineDrive Automation",
        model="LD-C320",
        location="Plant A / Assembly Line 3",
        status=MachineStatus.HEALTHY,
        temperature_limit=60.0,
        vibration_limit=3.0,
        motor_current_limit=8.0,
        notes="Variable-speed belt conveyor feeding assembly station 3.",
    )
    store.upsert_machine(conv_03)

    _add_telemetry(
        store,
        "PUMP-04",
        [
            ("2026-08-07T08:00:00Z", 58.0, 2.8, 10.2),
            ("2026-08-07T09:00:00Z", 59.5, 3.0, 10.5),
            ("2026-08-07T10:00:00Z", 60.0, 3.1, 10.8),
            ("2026-08-07T11:00:00Z", 59.0, 2.9, 10.4),
            ("2026-08-07T12:00:00Z", 60.5, 3.2, 10.9),
        ],
    )
    _add_telemetry(
        store,
        "CNC-02",
        [
            ("2026-08-07T08:00:00Z", 42.0, 1.4, 12.0),
            ("2026-08-07T09:00:00Z", 44.0, 1.5, 12.4),
            ("2026-08-07T10:00:00Z", 45.0, 1.6, 12.8),
            ("2026-08-07T11:00:00Z", 43.0, 1.4, 12.2),
            ("2026-08-07T12:00:00Z", 44.5, 1.5, 12.5),
        ],
    )
    _add_telemetry(
        store,
        "FAN-01",
        [
            ("2026-08-07T08:00:00Z", 34.0, 2.0, 6.2),
            ("2026-08-07T09:00:00Z", 35.0, 2.1, 6.4),
            ("2026-08-07T10:00:00Z", 36.0, 2.2, 6.5),
            ("2026-08-07T11:00:00Z", 35.5, 2.0, 6.3),
            ("2026-08-07T12:00:00Z", 34.5, 2.1, 6.4),
        ],
    )
    _add_telemetry(
        store,
        "CONV-03",
        [
            ("2026-08-07T08:00:00Z", 38.0, 1.2, 4.8),
            ("2026-08-07T09:00:00Z", 39.0, 1.3, 5.0),
            ("2026-08-07T10:00:00Z", 40.0, 1.3, 5.1),
            ("2026-08-07T11:00:00Z", 39.5, 1.2, 4.9),
            ("2026-08-07T12:00:00Z", 38.5, 1.2, 5.0),
        ],
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
    """Populate an in-memory store with fleet demo data.

    All machines (including PUMP-04) start HEALTHY with in-limit telemetry.
    Use the live simulator or /api/demo/* shortcuts to introduce failures.
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
