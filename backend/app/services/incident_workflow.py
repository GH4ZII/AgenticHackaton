"""Full incident workflow: telemetry → anomaly → auto agent investigation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.models.incident import Incident, IncidentStatus
from app.models.telemetry import TelemetrySample
from app.services.agent_runner import AgentRunResult, run_maintenance_agent
from app.services.anomaly_detector import AnomalyResult, detect_anomaly
from app.services.incident_enrichment import enrich_incident_diagnosis
from app.store.protocol import DomainStore


@dataclass
class WorkflowResult:
    anomaly: AnomalyResult
    agent_invoked: bool = False
    agent_skipped_reason: str | None = None
    agent_result: AgentRunResult | None = None
    incident: Incident | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _update_incident(store: DomainStore, incident: Incident) -> Incident:
    store.add_incident(incident)
    return incident


async def handle_telemetry(
    store: DomainStore,
    sample: TelemetrySample,
    *,
    invoke_agent: bool = True,
) -> WorkflowResult:
    """Process one telemetry sample through detection and optional agent run.

    Agent runs only when a **new** incident is created (idempotent for repeats).
    """
    anomaly = detect_anomaly(store, sample)
    if not anomaly.is_anomalous or anomaly.incident is None:
        return WorkflowResult(anomaly=anomaly, agent_invoked=False)

    incident = anomaly.incident

    if not anomaly.created:
        return WorkflowResult(
            anomaly=anomaly,
            agent_invoked=False,
            agent_skipped_reason="open_incident_already_exists",
            incident=incident,
        )

    if not invoke_agent:
        return WorkflowResult(
            anomaly=anomaly,
            agent_invoked=False,
            agent_skipped_reason="invoke_agent_disabled",
            incident=incident,
        )

    incident.status = IncidentStatus.INVESTIGATING
    _update_incident(store, incident)
    store.add_agent_action(
        {
            "timestamp": _now_iso(),
            "machine_id": incident.machine_id,
            "incident_id": incident.incident_id,
            "action": "investigation_started",
            "detail": f"Auto-started investigation for {incident.incident_id}",
        }
    )

    agent_result = await run_maintenance_agent(incident.machine_id, incident)

    incident.agent_summary = agent_result.final_text or (
        "Agent finished without text summary. "
        f"Tools called: {', '.join(agent_result.tool_calls) or 'none'}."
    )
    enrich_incident_diagnosis(store, incident)
    _update_incident(store, incident)
    store.add_agent_action(
        {
            "timestamp": _now_iso(),
            "machine_id": incident.machine_id,
            "incident_id": incident.incident_id,
            "action": "investigation_finished",
            "detail": (
                f"Tools: {', '.join(agent_result.tool_calls) or 'none'}. "
                f"Summary length: {len(incident.agent_summary)} chars."
            ),
        }
    )

    return WorkflowResult(
        anomaly=anomaly,
        agent_invoked=True,
        agent_result=agent_result,
        incident=incident,
    )


def handle_telemetry_sync(
    store: DomainStore,
    sample: TelemetrySample,
    **kwargs: Any,
) -> WorkflowResult:
    """Sync wrapper for scripts that prefer asyncio.run at the top level."""
    import asyncio

    return asyncio.run(handle_telemetry(store, sample, **kwargs))
