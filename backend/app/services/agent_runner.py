"""Run the Maintenance Agent via Google ADK (auto-generated prompts)."""

from __future__ import annotations

from dataclasses import dataclass, field

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.models.incident import Incident
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


async def _run_agent_with_prompt(
    prompt: str,
    *,
    user_id: str,
) -> AgentRunResult:
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

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "function_call", None):
                    tool_calls.append(part.function_call.name)
                elif getattr(part, "text", None):
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
) -> AgentRunResult:
    """Invoke the ADK maintenance agent for an anomaly incident."""
    prompt = build_anomaly_prompt(machine_id, incident)
    return await _run_agent_with_prompt(prompt, user_id=user_id)


async def run_verification_agent(
    machine_id: str,
    incident: Incident,
    work_order_id: str,
    *,
    user_id: str = "repair_verification",
) -> AgentRunResult:
    """Invoke the ADK agent to verify post-repair machine health."""
    prompt = build_verification_prompt(machine_id, incident, work_order_id)
    return await _run_agent_with_prompt(prompt, user_id=user_id)
