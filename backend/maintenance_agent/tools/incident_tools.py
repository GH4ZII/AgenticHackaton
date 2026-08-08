"""Incident resolution tools backed by the domain store."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.incident import IncidentStatus
from app.runtime import get_store


def resolve_incident(incident_id: str, summary: str = "") -> dict:
    """Mark an incident as RESOLVED after repair verification.

    Use this when post-repair telemetry is within normal operating limits
    and the related work order has been completed.

    Args:
        incident_id: Incident identifier, for example "INC-DEMO01".
        summary: Optional short verification note to store on the incident.

    Returns:
        Resolved incident payload, or an error/not-found payload.
    """
    store = get_store()
    incidents = {i.incident_id: i for i in store.list_incidents()}
    incident = incidents.get(incident_id)
    if incident is None and hasattr(store, "get_incident"):
        incident = store.get_incident(incident_id)
    if incident is None:
        return {
            "status": "not_found",
            "incident_id": incident_id,
            "message": f"No incident found for '{incident_id}'.",
        }

    if incident.status == IncidentStatus.RESOLVED:
        return {
            "status": "success",
            "incident": incident.model_dump(mode="json"),
            "message": "Incident was already resolved.",
        }

    now = datetime.now(timezone.utc)
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = now
    if summary.strip():
        note = summary.strip()
        if incident.agent_summary:
            incident.agent_summary = f"{incident.agent_summary}\n\nVerification: {note}"
        else:
            incident.agent_summary = note

    store.add_incident(incident)
    store.add_agent_action(
        {
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "machine_id": incident.machine_id,
            "incident_id": incident.incident_id,
            "action": "incident_resolved",
            "detail": summary.strip() or "Incident marked RESOLVED after verification.",
        }
    )

    return {
        "status": "success",
        "incident": incident.model_dump(mode="json"),
    }
