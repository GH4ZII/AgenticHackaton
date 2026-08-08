"""Phase 6 success check: Pub/Sub publish → pull → full workflow."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

ACTION_TOOLS = {
    "create_work_order",
    "notify_technician",
    "update_machine_status",
}


def _check_env() -> int | None:
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if not project or project.startswith("<"):
        print("Set GOOGLE_CLOUD_PROJECT in backend/.env")
        return 1

    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().upper() in {
        "1",
        "TRUE",
        "YES",
    }
    if use_vertex:
        if not os.getenv("GOOGLE_CLOUD_LOCATION"):
            print("Set GOOGLE_CLOUD_LOCATION for Vertex AI.")
            return 1
    elif not os.getenv("GOOGLE_API_KEY"):
        print("Set Vertex env vars or GOOGLE_API_KEY.")
        return 1
    return None


async def main() -> int:
    env_error = _check_env()
    if env_error is not None:
        return env_error

    # Clean one-shot demo: in-memory store so an open Firestore incident
    # does not skip the agent.
    os.environ["USE_FIRESTORE"] = "false"

    from app.runtime import reset_store
    from app.services.incident_workflow import handle_telemetry
    from app.services.pubsub_service import (
        acknowledge,
        ensure_topic_and_subscription,
        pull_telemetry,
        topic_id,
        subscription_id,
    )
    from app.services.simulator_service import publish_scenario

    store = reset_store()
    topic_path, sub_path = ensure_topic_and_subscription()
    print(f"Topic:        {topic_path}")
    print(f"Subscription: {sub_path}")
    print(f"Names:        topic={topic_id()} sub={subscription_id()}")
    print("Publishing BEARING_DEGRADATION event to Pub/Sub...")

    message_id, event = publish_scenario("BEARING_DEGRADATION")
    print(f"Published message_id={message_id}")
    print(f"Event: {event}")
    print("Pulling from subscription...")

    pulled = []
    deadline = time.time() + 45
    while time.time() < deadline and not pulled:
        pulled = pull_telemetry(max_messages=1, timeout=10.0)
        if not pulled:
            print("  (no message yet, retrying...)")
            time.sleep(2)

    if not pulled:
        print("FAIL: no Pub/Sub message received within timeout.")
        return 2

    msg = pulled[0]
    print(f"Pulled message_id={msg.message_id}")
    print(f"Sample: machine={msg.sample.machine_id} "
          f"temp={msg.sample.temperature_c} "
          f"vib={msg.sample.vibration_mm_s} "
          f"current={msg.sample.motor_current_a}")
    print("---")
    print("Running Phase 5 workflow from Pub/Sub payload (no manual prompt)...")

    result = await handle_telemetry(store, msg.sample)
    acknowledge([msg.ack_id])
    print("Acked Pub/Sub message.")

    if not result.anomaly.is_anomalous or result.incident is None:
        print("FAIL: expected anomaly + incident.")
        return 3

    print(
        f"Incident {result.incident.incident_id} "
        f"created={result.anomaly.created} agent_invoked={result.agent_invoked}"
    )

    if not result.agent_invoked or result.agent_result is None:
        print("FAIL: agent was not invoked via Pub/Sub-triggered workflow.")
        return 4

    tools = result.agent_result.tool_calls
    print(f"Tools called: {tools}")
    print("---")
    print(result.agent_result.final_text or "(no final text)")
    print("---")

    if not set(tools).intersection(ACTION_TOOLS):
        print("FAIL: expected at least one action tool.")
        return 5

    if not result.agent_result.final_text:
        print("FAIL: missing agent decision text.")
        return 6

    print(
        f"Work orders: {len(store.list_work_orders())} | "
        f"Notifications: {len(store.list_notifications())}"
    )
    print(
        "\nSUCCESS: Publishing an abnormal machine event triggered the complete workflow."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
