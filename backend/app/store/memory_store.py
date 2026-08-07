"""In-memory persistence for Phase 2/3 local development."""

from __future__ import annotations

from typing import Any

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
        self.maintenance_history: dict[str, list[dict[str, Any]]] = {}
        self.manuals: dict[str, list[dict[str, Any]]] = {}
        self.notifications: list[dict[str, Any]] = []
        self.agent_actions: list[dict[str, Any]] = []

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

    def list_work_orders(self) -> list[WorkOrder]:
        return list(self.work_orders.values())

    def get_work_order(self, work_order_id: str) -> WorkOrder | None:
        return self.work_orders.get(work_order_id)

    def upsert_inventory_item(self, item: InventoryItem) -> InventoryItem:
        self.inventory[item.part_id] = item
        return item

    def list_inventory(self) -> list[InventoryItem]:
        return list(self.inventory.values())

    def search_inventory(self, query: str) -> list[InventoryItem]:
        q = query.strip().lower()
        if not q:
            return self.list_inventory()
        matches: list[InventoryItem] = []
        for item in self.inventory.values():
            haystack = f"{item.name} {item.part_number} {item.part_id}".lower()
            if q in haystack:
                matches.append(item)
        return matches

    def set_maintenance_history(
        self, machine_id: str, entries: list[dict[str, Any]]
    ) -> None:
        self.maintenance_history[machine_id.strip().upper()] = entries

    def get_maintenance_history(self, machine_id: str) -> list[dict[str, Any]]:
        return list(self.maintenance_history.get(machine_id.strip().upper(), []))

    def set_manual_sections(
        self, machine_id: str, sections: list[dict[str, Any]]
    ) -> None:
        self.manuals[machine_id.strip().upper()] = sections

    def has_manual(self, machine_id: str) -> bool:
        return machine_id.strip().upper() in self.manuals

    def search_manual(self, machine_id: str, query: str) -> list[dict[str, Any]]:
        sections = self.manuals.get(machine_id.strip().upper(), [])
        q = query.strip().lower()
        if not q:
            return list(sections)
        return [
            section
            for section in sections
            if q in section.get("title", "").lower()
            or q in section.get("content", "").lower()
            or any(q in tag.lower() for tag in section.get("tags", []))
        ]

    def add_notification(self, notification: dict[str, Any]) -> dict[str, Any]:
        self.notifications.append(notification)
        return notification

    def list_notifications(self) -> list[dict[str, Any]]:
        return list(self.notifications)

    def add_agent_action(self, action: dict[str, Any]) -> dict[str, Any]:
        self.agent_actions.append(action)
        return action

    def list_agent_actions(self) -> list[dict[str, Any]]:
        return list(self.agent_actions)

    def clear(self) -> None:
        self.machines.clear()
        self.telemetry.clear()
        self.incidents.clear()
        self.work_orders.clear()
        self.inventory.clear()
        self.maintenance_history.clear()
        self.manuals.clear()
        self.notifications.clear()
        self.agent_actions.clear()
