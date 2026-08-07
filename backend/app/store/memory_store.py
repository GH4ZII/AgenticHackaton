"""In-memory persistence for Phase 2 local development."""

from __future__ import annotations

from app.models.incident import Incident, IncidentStatus
from app.models.inventory import InventoryItem
from app.models.machine import Machine
from app.models.telemetry import TelemetrySample
from app.models.work_order import WorkOrder


class MemoryStore:
    """Simple dict-backed store. Replaced by Firestore in Phase 4."""

    def __init__(self) -> None:
        self.machines: dict[str, Machine] = {}
        self.telemetry: list[TelemetrySample] = []
        self.incidents: dict[str, Incident] = {}
        self.work_orders: dict[str, WorkOrder] = {}
        self.inventory: dict[str, InventoryItem] = {}

    def upsert_machine(self, machine: Machine) -> Machine:
        self.machines[machine.machine_id] = machine
        return machine

    def get_machine(self, machine_id: str) -> Machine | None:
        return self.machines.get(machine_id.strip().upper())

    def add_telemetry(self, sample: TelemetrySample) -> TelemetrySample:
        self.telemetry.append(sample)
        return sample

    def get_telemetry_for_machine(self, machine_id: str) -> list[TelemetrySample]:
        normalized = machine_id.strip().upper()
        return [s for s in self.telemetry if s.machine_id.upper() == normalized]

    def add_incident(self, incident: Incident) -> Incident:
        self.incidents[incident.incident_id] = incident
        return incident

    def get_open_incident_for_machine(self, machine_id: str) -> Incident | None:
        normalized = machine_id.strip().upper()
        for incident in self.incidents.values():
            if (
                incident.machine_id.upper() == normalized
                and incident.status != IncidentStatus.RESOLVED
            ):
                return incident
        return None

    def list_incidents(self) -> list[Incident]:
        return list(self.incidents.values())

    def upsert_work_order(self, work_order: WorkOrder) -> WorkOrder:
        self.work_orders[work_order.work_order_id] = work_order
        return work_order

    def upsert_inventory_item(self, item: InventoryItem) -> InventoryItem:
        self.inventory[item.part_id] = item
        return item

    def list_inventory(self) -> list[InventoryItem]:
        return list(self.inventory.values())

    def clear(self) -> None:
        self.machines.clear()
        self.telemetry.clear()
        self.incidents.clear()
        self.work_orders.clear()
        self.inventory.clear()
