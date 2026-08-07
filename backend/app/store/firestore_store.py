"""Firestore-backed domain store (Phase 4)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.incident import Incident, IncidentStatus
from app.models.inventory import InventoryItem
from app.models.machine import Machine
from app.models.telemetry import TelemetrySample
from app.models.work_order import WorkOrder
from app.services.firestore_service import get_firestore_client


def _to_plain(data: dict[str, Any]) -> dict[str, Any]:
    """Convert Pydantic json-mode dict into Firestore-friendly values."""
    plain: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            plain[key] = value
        else:
            plain[key] = value
    return plain


class FirestoreStore:
    """Persist domain entities in Cloud Firestore."""

    def __init__(self, client: firestore.Client | None = None) -> None:
        self._db = client or get_firestore_client()

    @property
    def client(self) -> firestore.Client:
        return self._db

    def upsert_machine(self, machine: Machine) -> Machine:
        data = _to_plain(machine.model_dump(mode="json"))
        self._db.collection("machines").document(machine.machine_id).set(data)
        return machine

    def get_machine(self, machine_id: str) -> Machine | None:
        doc = self._db.collection("machines").document(machine_id.strip().upper()).get()
        if not doc.exists:
            return None
        return Machine.model_validate(doc.to_dict())

    def add_telemetry(self, sample: TelemetrySample) -> TelemetrySample:
        data = _to_plain(sample.model_dump(mode="json"))
        # Stable-ish id for demo seed rows; unique enough for runtime samples.
        ts = sample.timestamp.strftime("%Y%m%dT%H%M%SZ")
        doc_id = f"{sample.machine_id}_{ts}_{sample.vibration_mm_s}"
        self._db.collection("telemetry").document(doc_id).set(data)
        return sample

    def get_telemetry_for_machine(self, machine_id: str) -> list[TelemetrySample]:
        normalized = machine_id.strip().upper()
        query = self._db.collection("telemetry").where(
            filter=FieldFilter("machine_id", "==", normalized)
        )
        samples = [TelemetrySample.model_validate(doc.to_dict()) for doc in query.stream()]
        return sorted(samples, key=lambda s: s.timestamp)

    def add_incident(self, incident: Incident) -> Incident:
        data = _to_plain(incident.model_dump(mode="json"))
        self._db.collection("incidents").document(incident.incident_id).set(data)
        return incident

    def get_incident(self, incident_id: str) -> Incident | None:
        doc = self._db.collection("incidents").document(incident_id).get()
        if not doc.exists:
            return None
        return Incident.model_validate(doc.to_dict())

    def get_open_incident_for_machine(self, machine_id: str) -> Incident | None:
        normalized = machine_id.strip().upper()
        query = self._db.collection("incidents").where(
            filter=FieldFilter("machine_id", "==", normalized)
        )
        open_incidents: list[Incident] = []
        for doc in query.stream():
            incident = Incident.model_validate(doc.to_dict())
            if incident.status != IncidentStatus.RESOLVED:
                open_incidents.append(incident)
        if not open_incidents:
            return None
        return max(open_incidents, key=lambda i: i.detected_at)

    def list_incidents(self) -> list[Incident]:
        return [
            Incident.model_validate(doc.to_dict())
            for doc in self._db.collection("incidents").stream()
        ]

    def upsert_work_order(self, work_order: WorkOrder) -> WorkOrder:
        data = _to_plain(work_order.model_dump(mode="json"))
        self._db.collection("work_orders").document(work_order.work_order_id).set(data)
        return work_order

    def get_work_order(self, work_order_id: str) -> WorkOrder | None:
        doc = self._db.collection("work_orders").document(work_order_id).get()
        if not doc.exists:
            return None
        return WorkOrder.model_validate(doc.to_dict())

    def list_work_orders(self) -> list[WorkOrder]:
        return [
            WorkOrder.model_validate(doc.to_dict())
            for doc in self._db.collection("work_orders").stream()
        ]

    def upsert_inventory_item(self, item: InventoryItem) -> InventoryItem:
        data = _to_plain(item.model_dump(mode="json"))
        self._db.collection("inventory").document(item.part_id).set(data)
        return item

    def list_inventory(self) -> list[InventoryItem]:
        return [
            InventoryItem.model_validate(doc.to_dict())
            for doc in self._db.collection("inventory").stream()
        ]

    def search_inventory(self, query: str) -> list[InventoryItem]:
        q = query.strip().lower()
        items = self.list_inventory()
        if not q:
            return items
        return [
            item
            for item in items
            if q in f"{item.name} {item.part_number} {item.part_id}".lower()
        ]

    def set_maintenance_history(
        self, machine_id: str, entries: list[dict[str, Any]]
    ) -> None:
        normalized = machine_id.strip().upper()
        existing = self._db.collection("maintenance_history").where(
            filter=FieldFilter("machine_id", "==", normalized)
        )
        batch = self._db.batch()
        for doc in existing.stream():
            batch.delete(doc.reference)
        for index, entry in enumerate(entries):
            doc_id = f"{normalized}_{index}"
            payload = {"machine_id": normalized, "index": index, **entry}
            batch.set(self._db.collection("maintenance_history").document(doc_id), payload)
        batch.commit()

    def get_maintenance_history(self, machine_id: str) -> list[dict[str, Any]]:
        normalized = machine_id.strip().upper()
        query = self._db.collection("maintenance_history").where(
            filter=FieldFilter("machine_id", "==", normalized)
        )
        rows = list(query.stream())
        rows.sort(key=lambda d: d.to_dict().get("index", 0))
        results: list[dict[str, Any]] = []
        for doc in rows:
            data = doc.to_dict() or {}
            data.pop("machine_id", None)
            data.pop("index", None)
            results.append(data)
        return results

    def set_manual_sections(
        self, machine_id: str, sections: list[dict[str, Any]]
    ) -> None:
        normalized = machine_id.strip().upper()
        existing = self._db.collection("manuals").where(
            filter=FieldFilter("machine_id", "==", normalized)
        )
        batch = self._db.batch()
        for doc in existing.stream():
            batch.delete(doc.reference)
        for section in sections:
            section_id = section.get("section_id", "section")
            doc_id = f"{normalized}_{section_id}"
            payload = {"machine_id": normalized, **section}
            batch.set(self._db.collection("manuals").document(doc_id), payload)
        batch.commit()

    def has_manual(self, machine_id: str) -> bool:
        normalized = machine_id.strip().upper()
        docs = (
            self._db.collection("manuals")
            .where(filter=FieldFilter("machine_id", "==", normalized))
            .limit(1)
            .stream()
        )
        return any(True for _ in docs)

    def search_manual(self, machine_id: str, query: str) -> list[dict[str, Any]]:
        normalized = machine_id.strip().upper()
        docs = (
            self._db.collection("manuals")
            .where(filter=FieldFilter("machine_id", "==", normalized))
            .stream()
        )
        sections: list[dict[str, Any]] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data.pop("machine_id", None)
            sections.append(data)
        q = query.strip().lower()
        if not q:
            return sections
        return [
            section
            for section in sections
            if q in section.get("title", "").lower()
            or q in section.get("content", "").lower()
            or any(q in tag.lower() for tag in section.get("tags", []))
        ]

    def add_notification(self, notification: dict[str, Any]) -> dict[str, Any]:
        notification_id = notification.get("notification_id")
        if not notification_id:
            raise ValueError("notification_id is required")
        self._db.collection("notifications").document(notification_id).set(notification)
        return notification

    def list_notifications(self) -> list[dict[str, Any]]:
        return [doc.to_dict() or {} for doc in self._db.collection("notifications").stream()]

    def add_agent_action(self, action: dict[str, Any]) -> dict[str, Any]:
        _, doc_ref = self._db.collection("agent_actions").add(action)
        stored = dict(action)
        stored["action_id"] = doc_ref.id
        doc_ref.set(stored)
        return stored

    def list_agent_actions(self) -> list[dict[str, Any]]:
        return [doc.to_dict() or {} for doc in self._db.collection("agent_actions").stream()]

    def is_empty(self) -> bool:
        """True when no machines exist yet (used for idempotent seed)."""
        docs = self._db.collection("machines").limit(1).stream()
        return not any(True for _ in docs)

    def clear(self) -> None:
        """Delete all known demo collections. Use only in tests."""
        for name in (
            "machines",
            "telemetry",
            "incidents",
            "work_orders",
            "inventory",
            "maintenance_history",
            "manuals",
            "notifications",
            "agent_actions",
        ):
            self._delete_collection(name)

    def _delete_collection(self, collection_name: str, batch_size: int = 100) -> None:
        coll = self._db.collection(collection_name)
        while True:
            docs = list(coll.limit(batch_size).stream())
            if not docs:
                return
            batch = self._db.batch()
            for doc in docs:
                batch.delete(doc.reference)
            batch.commit()
