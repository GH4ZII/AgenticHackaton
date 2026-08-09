"""Run the Maintenance Agent via Google ADK (auto-generated prompts)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.models.incident import Incident
from app.runtime import get_store
from app.services.agent_progress import (
    emit_agent_action,
    summarize_tool_response,
    tool_label,
)
from app.store.protocol import DomainStore
from maintenance_agent.agent import root_agent


@dataclass
class AgentRunResult:
    prompt: str
    tool_calls: list[str] = field(default_factory=list)
    final_text: str = ""


def build_anomaly_prompt(machine_id: str, incident: Incident) -> str:
    """Build the system-triggered investigation prompt (no human typing)."""
    return (
        f"Anomaly detected on {machine_id}. "
        f"Incident {incident.incident_id} is OPEN with severity "
        f"{incident.severity.value}. "
        f"Trigger: {incident.trigger_reason}. "
        "Investigate using tools and take required maintenance actions."
    )


def build_verification_prompt(
    machine_id: str,
    incident: Incident,
    work_order_id: str,
) -> str:
    """Build the post-repair verification prompt."""
    return (
        f"Work order {work_order_id} for {machine_id} was marked COMPLETED. "
        f"Incident {incident.incident_id} needs repair verification. "
        "Retrieve current machine context and telemetry. "
        "If readings are within normal operating limits, resolve the incident "
        "and set machine status to HEALTHY. "
        "If still abnormal, do not resolve and explain why."
    )


def _parse_function_response(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    # google.genai types sometimes expose .response as Struct-like
    if hasattr(raw, "items"):
        try:
            return dict(raw.items())  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            pass
    return str(raw)


async def _run_agent_with_prompt(
    prompt: str,
    *,
    user_id: str,
    machine_id: str | None = None,
    incident_id: str | None = None,
    store: DomainStore | None = None,
) -> AgentRunResult:
    domain = store or get_store()
    runner = InMemoryRunner(agent=root_agent, app_name="maintenance_agent")
    session = await runner.session_service.create_session(
        app_name="maintenance_agent",
        user_id=user_id,
    )
    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    tool_calls: list[str] = []
    final_text_parts: list[str] = []
    pending_tools: dict[str, str] = {}

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=message,
    ):
        if not (event.content and event.content.parts):
            continue
        for part in event.content.parts:
            fn_call = getattr(part, "function_call", None)
            if fn_call and getattr(fn_call, "name", None):
                name = str(fn_call.name)
                tool_calls.append(name)
                label = tool_label(name, done=False)
                if machine_id:
                    emit_agent_action(
                        domain,
                        machine_id=machine_id,
                        incident_id=incident_id,
                        action="tool_started",
                        detail=f"Calling {name}",
                        label=label,
                        status="running",
                        step_kind="tool",
                        tool_name=name,
                    )
                pending_tools[name] = label
                continue

            fn_resp = getattr(part, "function_response", None)
            if fn_resp and getattr(fn_resp, "name", None):
                name = str(fn_resp.name)
                raw = getattr(fn_resp, "response", None)
                parsed = _parse_function_response(raw)
                detail = summarize_tool_response(name, parsed)
                if machine_id:
                    emit_agent_action(
                        domain,
                        machine_id=machine_id,
                        incident_id=incident_id,
                        action="tool_completed",
                        detail=detail,
                        label=tool_label(name, done=True),
                        status="completed",
                        step_kind="tool",
                        tool_name=name,
                    )
                pending_tools.pop(name, None)
                continue

            text = getattr(part, "text", None)
            if text:
                final_text_parts.append(part.text)

    return AgentRunResult(
        prompt=prompt,
        tool_calls=tool_calls,
        final_text="\n".join(final_text_parts).strip(),
    )


async def run_maintenance_agent(
    machine_id: str,
    incident: Incident,
    *,
    user_id: str = "incident_workflow",
    store: DomainStore | None = None,
) -> AgentRunResult:
    """Invoke the ADK maintenance agent for an anomaly incident."""
    prompt = build_anomaly_prompt(machine_id, incident)
    return await _run_agent_with_prompt(
        prompt,
        user_id=user_id,
        machine_id=machine_id,
        incident_id=incident.incident_id,
        store=store,
    )


async def run_verification_agent(
    machine_id: str,
    incident: Incident,
    work_order_id: str,
    *,
    user_id: str = "repair_verification",
    store: DomainStore | None = None,
) -> AgentRunResult:
    """Invoke the ADK agent to verify post-repair machine health."""
    prompt = build_verification_prompt(machine_id, incident, work_order_id)
    return await _run_agent_with_prompt(
        prompt,
        user_id=user_id,
        machine_id=machine_id,
        incident_id=incident.incident_id,
        store=store,
    )
