"""Incident read APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.serializers import incident_to_dict, work_order_to_dict
from app.runtime import get_store

router = APIRouter(prefix="/api", tags=["incidents"])


@router.get("/incidents")
def list_incidents() -> dict:
    store = get_store()
    incidents = [incident_to_dict(i) for i in store.list_incidents()]
    incidents.sort(key=lambda i: i.get("detected_at") or "", reverse=True)
    return {"incidents": incidents, "count": len(incidents)}


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str) -> dict:
    store = get_store()
    incidents = {i.incident_id: i for i in store.list_incidents()}
    incident = incidents.get(incident_id)
    if incident is None:
        # Firestore may need direct get - MemoryStore has dict
        if hasattr(store, "incidents") and incident_id in store.incidents:
            incident = store.incidents[incident_id]
        elif hasattr(store, "get_incident"):
            incident = store.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")

    related_wos = [
        work_order_to_dict(w)
        for w in store.list_work_orders()
        if w.incident_id == incident.incident_id
        or (
            w.machine_id == incident.machine_id
            and w.status.value in {"OPEN", "IN_PROGRESS"}
        )
    ]
    actions = [
        a
        for a in store.list_agent_actions()
        if a.get("incident_id") == incident.incident_id
        or a.get("machine_id") == incident.machine_id
    ]
    actions.sort(key=lambda a: a.get("timestamp") or "")

    inventory = [
        item.model_dump(mode="json")
        for item in store.list_inventory()
    ]

    return {
        "incident": incident_to_dict(incident),
        "work_orders": related_wos,
        "agent_actions": actions,
        "inventory": inventory,
    }
