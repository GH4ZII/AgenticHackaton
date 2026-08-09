"""Full incident workflow: telemetry → anomaly → auto agent investigation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from app.models.incident import Incident, IncidentStatus
from app.models.telemetry import TelemetrySample
from app.services.agent_progress import emit_agent_action
from app.services.agent_runner import AgentRunResult, run_maintenance_agent
from app.services.anomaly_detector import AnomalyResult, detect_anomaly
from app.services.incident_enrichment import enrich_incident_diagnosis
from app.store.protocol import DomainStore

logger = logging.getLogger(__name__)

# Keep strong refs so background investigations are not garbage-collected.
_background_tasks: set[asyncio.Task[None]] = set()


@dataclass
class WorkflowResult:
    anomaly: AnomalyResult
    agent_invoked: bool = False
    agent_skipped_reason: str | None = None
    agent_result: AgentRunResult | None = None
    incident: Incident | None = None
    agent_pending: bool = False


def _update_incident(store: DomainStore, incident: Incident) -> Incident:
    store.add_incident(incident)
    return incident


async def _complete_investigation(
    store: DomainStore,
    incident: Incident,
) -> AgentRunResult:
    """Run the agent and persist summary / finished action."""
    agent_result = await run_maintenance_agent(
        incident.machine_id,
        incident,
        store=store,
    )

    # Re-load in case tools already mutated the incident.
    current = store.get_incident(incident.incident_id) or incident
    current.agent_summary = agent_result.final_text or (
        "Agent finished without text summary. "
        f"Tools called: {', '.join(agent_result.tool_calls) or 'none'}."
    )
    enrich_incident_diagnosis(store, current)
    _update_incident(store, current)
    emit_agent_action(
        store,
        machine_id=current.machine_id,
        incident_id=current.incident_id,
        action="investigation_finished",
        detail=(
            f"Tools: {', '.join(agent_result.tool_calls) or 'none'}. "
            f"Summary length: {len(current.agent_summary)} chars."
        ),
        label="Investigation complete",
        status="completed",
        step_kind="lifecycle",
    )
    return agent_result


def _schedule_investigation(store: DomainStore, incident: Incident) -> None:
    async def _runner() -> None:
        try:
            await _complete_investigation(store, incident)
        except Exception:  # noqa: BLE001 — surface in logs; keep simulator alive
            logger.exception(
                "Background investigation failed for %s",
                incident.incident_id,
            )
            emit_agent_action(
                store,
                machine_id=incident.machine_id,
                incident_id=incident.incident_id,
                action="investigation_failed",
                detail="Agent investigation failed; see server logs.",
                label="Investigation failed",
                status="failed",
                step_kind="lifecycle",
            )

    task = asyncio.create_task(
        _runner(),
        name=f"investigate-{incident.incident_id}",
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def handle_telemetry(
    store: DomainStore,
    sample: TelemetrySample,
    *,
    invoke_agent: bool = True,
    wait_for_agent: bool = True,
) -> WorkflowResult:
    """Process one telemetry sample through detection and optional agent run.

    Agent runs only when a **new** incident is created (idempotent for repeats).

    When ``wait_for_agent`` is False, the incident is persisted immediately and
    the agent continues in the background so the API/UI stay responsive.
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
    emit_agent_action(
        store,
        machine_id=incident.machine_id,
        incident_id=incident.incident_id,
        action="anomaly_detected",
        detail=incident.trigger_reason,
        label="Anomaly detected",
        status="completed",
        step_kind="lifecycle",
    )
    emit_agent_action(
        store,
        machine_id=incident.machine_id,
        incident_id=incident.incident_id,
        action="investigation_started",
        detail=f"Auto-started investigation for {incident.incident_id}",
        label="Investigation started",
        status="completed",
        step_kind="lifecycle",
    )

    if not wait_for_agent:
        _schedule_investigation(store, incident)
        return WorkflowResult(
            anomaly=anomaly,
            agent_invoked=True,
            agent_pending=True,
            incident=incident,
        )

    agent_result = await _complete_investigation(store, incident)

    return WorkflowResult(
        anomaly=anomaly,
        agent_invoked=True,
        agent_result=agent_result,
        incident=store.get_incident(incident.incident_id) or incident,
    )


def handle_telemetry_sync(
    store: DomainStore,
    sample: TelemetrySample,
    **kwargs: Any,
) -> WorkflowResult:
    """Sync wrapper for scripts that prefer asyncio.run at the top level."""
    return asyncio.run(handle_telemetry(store, sample, **kwargs))
