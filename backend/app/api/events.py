"""Telemetry event endpoints (Pub/Sub push-ready)."""

from __future__ import annotations

import base64
import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.runtime import get_store
from app.services.incident_workflow import handle_telemetry
from app.services.pubsub_service import event_to_telemetry_sample

router = APIRouter(tags=["events"])


class PubSubMessage(BaseModel):
    data: str
    messageId: str | None = None
    publishTime: str | None = None
    attributes: dict[str, str] | None = None


class PubSubPushEnvelope(BaseModel):
    message: PubSubMessage
    subscription: str | None = None


class TelemetryEventBody(BaseModel):
    machine_id: str
    timestamp: str
    temperature: float | None = None
    vibration: float | None = None
    motor_current: float | None = None
    temperature_c: float | None = None
    vibration_mm_s: float | None = None
    motor_current_a: float | None = None


def _decode_pubsub_data(data_b64: str) -> dict[str, Any]:
    raw = base64.b64decode(data_b64).decode("utf-8")
    return json.loads(raw)


@router.post("/events/telemetry")
async def receive_telemetry(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept Pub/Sub push envelopes or raw telemetry JSON.

    Pub/Sub push format:
      {"message": {"data": "<base64 json>", ...}, "subscription": "..."}

    Raw format (local testing):
      {"machine_id": "PUMP-04", "timestamp": "...", "temperature": 86.0, ...}
    """
    try:
        if "message" in payload and isinstance(payload["message"], dict):
            envelope = PubSubPushEnvelope.model_validate(payload)
            event = _decode_pubsub_data(envelope.message.data)
        else:
            event = TelemetryEventBody.model_validate(payload).model_dump(
                exclude_none=True
            )
        sample = event_to_telemetry_sample(event)
    except Exception as exc:  # noqa: BLE001 - return clean 400 to callers
        raise HTTPException(status_code=400, detail=f"Invalid telemetry event: {exc}") from exc

    store = get_store()
    try:
        result = await handle_telemetry(store, sample, wait_for_agent=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "ok",
        "machine_id": sample.machine_id,
        "anomalous": result.anomaly.is_anomalous,
        "incident_created": result.anomaly.created,
        "agent_invoked": result.agent_invoked,
        "agent_skipped_reason": result.agent_skipped_reason,
        "incident_id": result.incident.incident_id if result.incident else None,
        "tools_called": (
            result.agent_result.tool_calls if result.agent_result else []
        ),
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
