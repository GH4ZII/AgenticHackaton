"""Google Pub/Sub helpers for telemetry events (Phase 6)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1

from app.models.telemetry import TelemetrySample


@dataclass
class PulledTelemetry:
    sample: TelemetrySample
    ack_id: str
    message_id: str
    raw: dict[str, Any]


def _project_id() -> str:
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    if not project or project.startswith("<"):
        raise ValueError("GOOGLE_CLOUD_PROJECT must be set for Pub/Sub.")
    return project


def topic_id() -> str:
    return os.getenv("PUBSUB_TOPIC", "machine-telemetry-events").strip()


def subscription_id() -> str:
    return os.getenv(
        "PUBSUB_SUBSCRIPTION", "machine-telemetry-events-worker"
    ).strip()


def ensure_topic_and_subscription(
    project_id: str | None = None,
    topic: str | None = None,
    subscription: str | None = None,
) -> tuple[str, str]:
    """Create topic + pull subscription if they do not already exist."""
    project = project_id or _project_id()
    topic_name = topic or topic_id()
    sub_name = subscription or subscription_id()

    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    topic_path = publisher.topic_path(project, topic_name)
    subscription_path = subscriber.subscription_path(project, sub_name)

    try:
        publisher.create_topic(request={"name": topic_path})
    except AlreadyExists:
        pass

    try:
        subscriber.create_subscription(
            request={"name": subscription_path, "topic": topic_path}
        )
    except AlreadyExists:
        pass

    return topic_path, subscription_path


def event_to_telemetry_sample(event: dict[str, Any]) -> TelemetrySample:
    """Map Pub/Sub event JSON to TelemetrySample."""
    payload = {
        "machine_id": event["machine_id"],
        "timestamp": event["timestamp"],
        "temperature_c": event.get("temperature_c", event.get("temperature")),
        "vibration_mm_s": event.get("vibration_mm_s", event.get("vibration")),
        "motor_current_a": event.get(
            "motor_current_a", event.get("motor_current")
        ),
    }
    return TelemetrySample.model_validate(payload)


def publish_telemetry(
    event: dict[str, Any],
    *,
    project_id: str | None = None,
    topic: str | None = None,
) -> str:
    """Publish a telemetry event dict to Pub/Sub. Returns message id."""
    project = project_id or _project_id()
    topic_name = topic or topic_id()
    ensure_topic_and_subscription(project, topic_name, subscription_id())

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic_name)
    data = json.dumps(event).encode("utf-8")
    future = publisher.publish(
        topic_path,
        data,
        machine_id=str(event.get("machine_id", "")),
    )
    return future.result(timeout=30)


def pull_telemetry(
    *,
    max_messages: int = 1,
    timeout: float = 30.0,
    project_id: str | None = None,
    subscription: str | None = None,
) -> list[PulledTelemetry]:
    """Pull telemetry messages from the worker subscription (no auto-ack)."""
    project = project_id or _project_id()
    sub_name = subscription or subscription_id()
    ensure_topic_and_subscription(project, topic_id(), sub_name)

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project, sub_name)

    response = subscriber.pull(
        request={
            "subscription": subscription_path,
            "max_messages": max_messages,
        },
        timeout=timeout,
    )

    results: list[PulledTelemetry] = []
    for received in response.received_messages:
        raw = json.loads(received.message.data.decode("utf-8"))
        sample = event_to_telemetry_sample(raw)
        results.append(
            PulledTelemetry(
                sample=sample,
                ack_id=received.ack_id,
                message_id=received.message.message_id,
                raw=raw,
            )
        )
    return results


def acknowledge(
    ack_ids: list[str],
    *,
    project_id: str | None = None,
    subscription: str | None = None,
) -> None:
    if not ack_ids:
        return
    project = project_id or _project_id()
    sub_name = subscription or subscription_id()
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project, sub_name)
    subscriber.acknowledge(
        request={"subscription": subscription_path, "ack_ids": ack_ids}
    )
