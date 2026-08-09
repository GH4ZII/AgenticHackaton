"""Human-readable labels and helpers for live investigation timeline events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.store.protocol import DomainStore

TOOL_LABELS: dict[str, str] = {
    "get_machine_context": "Loading machine context",
    "get_telemetry_history": "Analyzing recent sensor history",
    "get_maintenance_history": "Checking maintenance records",
    "search_machine_manual": "Consulting machine manual",
    "check_inventory": "Checking spare parts",
    "create_work_order": "Creating maintenance recommendation",
    "notify_technician": "Notifying technician",
    "update_machine_status": "Updating machine status",
    "request_shutdown_approval": "Requesting shutdown approval",
    "resolve_incident": "Resolving incident",
}

TOOL_DONE_LABELS: dict[str, str] = {
    "get_machine_context": "Machine context loaded",
    "get_telemetry_history": "Sensor history analyzed",
    "get_maintenance_history": "Maintenance records checked",
    "search_machine_manual": "Manual guidance reviewed",
    "check_inventory": "Spare parts availability checked",
    "create_work_order": "Work order created",
    "notify_technician": "Technician notified",
    "update_machine_status": "Machine status updated",
    "request_shutdown_approval": "Shutdown approval requested",
    "resolve_incident": "Incident resolved",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def tool_label(tool_name: str, *, done: bool = False) -> str:
    mapping = TOOL_DONE_LABELS if done else TOOL_LABELS
    return mapping.get(tool_name, tool_name.replace("_", " ").capitalize())


def summarize_tool_response(tool_name: str, response: Any) -> str:
    """Short UI-friendly detail from a tool response payload."""
    data = response
    if isinstance(response, dict) and "response" in response and len(response) <= 2:
        data = response.get("response", response)

    if not isinstance(data, dict):
        text = str(data)
        return text[:160] + ("…" if len(text) > 160 else "")

    status = data.get("status")
    if tool_name == "get_telemetry_history":
        telemetry = data.get("telemetry") or {}
        samples = telemetry.get("samples") or []
        trend = telemetry.get("trend") or {}
        summary = trend.get("summary")
        if summary:
            return str(summary)
        if samples:
            latest = samples[-1]
            return (
                f"{len(samples)} samples; latest vibration "
                f"{latest.get('vibration_mm_s', '?')} mm/s, "
                f"temp {latest.get('temperature_c', '?')} C"
            )
    if tool_name == "get_maintenance_history":
        history = data.get("history") or []
        last = data.get("last_inspection")
        if last:
            return f"{len(history)} records; last inspection {last.get('date', '')}"
        return f"{len(history)} maintenance records loaded"
    if tool_name == "create_work_order":
        wo_id = data.get("work_order_id") or (data.get("work_order") or {}).get(
            "work_order_id"
        )
        if wo_id:
            return f"Work order {wo_id} created"
    if tool_name == "check_inventory":
        items = data.get("matches") or data.get("items") or data.get("inventory") or []
        if isinstance(items, list):
            return f"{len(items)} matching part(s)"
    if tool_name == "search_machine_manual":
        hits = data.get("results") or data.get("sections") or []
        if isinstance(hits, list) and hits:
            return f"Found {len(hits)} relevant manual section(s)"
    if status:
        return f"status={status}"
    message = data.get("message")
    if message:
        return str(message)[:160]
    return "Completed"


def emit_agent_action(
    store: DomainStore,
    *,
    machine_id: str,
    incident_id: str | None,
    action: str,
    detail: str,
    label: str,
    status: str,
    step_kind: str = "tool",
    tool_name: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "timestamp": _now_iso(),
        "machine_id": machine_id,
        "incident_id": incident_id,
        "action": action,
        "detail": detail,
        "label": label,
        "status": status,
        "step_kind": step_kind,
    }
    if tool_name:
        payload["tool_name"] = tool_name
    return store.add_agent_action(payload)
