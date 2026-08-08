"""Phase 5 success check: abnormal telemetry auto-triggers the agent (no manual prompt)."""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
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


def _check_vertex_env() -> int | None:
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().upper() in {
        "1",
        "TRUE",
        "YES",
    }
    if use_vertex:
        required = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION"]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            print(f"Missing env vars for Vertex: {', '.join(missing)}")
            return 1
        if os.getenv("GOOGLE_CLOUD_PROJECT", "").startswith("<"):
            print("Set GOOGLE_CLOUD_PROJECT in backend/.env to a real GCP project ID.")
            return 1
        return None
    if not os.getenv("GOOGLE_API_KEY"):
        print(
            "Set GOOGLE_GENAI_USE_VERTEXAI=TRUE with project/location, "
            "or provide GOOGLE_API_KEY for Gemini API."
        )
        return 1
    return None


async def main() -> int:
    env_error = _check_vertex_env()
    if env_error is not None:
        return env_error

    # Phase 5 demo uses in-memory store for a clean one-shot workflow.
    os.environ["USE_FIRESTORE"] = "false"

    from app.models.telemetry import TelemetrySample
    from app.runtime import reset_store
    from app.services.incident_workflow import handle_telemetry

    store = reset_store()
    print("Seeded store for Phase 5 (in-memory).")
    print("No manual prompt will be typed.")
    print("Feeding abnormal telemetry into handle_telemetry()...")
    print("---")

    abnormal = TelemetrySample(
        machine_id="PUMP-04",
        timestamp=datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc),
        temperature_c=86.0,
        vibration_mm_s=8.7,
        motor_current_a=14.0,
    )
    result = await handle_telemetry(store, abnormal)

    if not result.anomaly.is_anomalous or result.incident is None:
        print("FAIL: expected anomaly + incident from abnormal telemetry.")
        return 2

    print(f"Incident: {result.incident.incident_id} status={result.incident.status.value}")
    print(f"Created new incident: {result.anomaly.created}")
    print(f"Agent invoked: {result.agent_invoked}")

    if not result.agent_invoked or result.agent_result is None:
        print("FAIL: agent was not auto-invoked for the new incident.")
        return 3

    agent = result.agent_result
    print(f"Auto prompt: {agent.prompt}")
    print(f"Tools called: {agent.tool_calls or '(none)'}")
    print("---")
    print(agent.final_text or "(no final text)")
    print("---")

    unique_tools = set(agent.tool_calls)
    if not unique_tools.intersection(ACTION_TOOLS):
        print(
            "FAIL: expected at least one action tool "
            f"({', '.join(sorted(ACTION_TOOLS))})."
        )
        return 4

    if not agent.final_text:
        print("FAIL: agent produced no decision text.")
        return 5

    if not result.incident.agent_summary:
        print("FAIL: incident.agent_summary was not saved.")
        return 6

    # Idempotency: second abnormal sample must not re-invoke the agent.
    second = await handle_telemetry(
        store,
        TelemetrySample(
            machine_id="PUMP-04",
            timestamp=datetime(2026, 8, 8, 12, 5, tzinfo=timezone.utc),
            temperature_c=87.0,
            vibration_mm_s=8.9,
            motor_current_a=14.2,
        ),
    )
    if second.agent_invoked:
        print("FAIL: agent ran again on existing open incident (not idempotent).")
        return 7
    print(
        f"Idempotent skip on second sample: {second.agent_skipped_reason}"
    )

    # Prove get_store() tools saw the same world (work orders / notifications).
    work_orders = store.list_work_orders()
    notifications = store.list_notifications()
    print(f"Work orders after workflow: {len(work_orders)}")
    print(f"Notifications after workflow: {len(notifications)}")

    print("\nSUCCESS: No manual prompt required — telemetry triggered the full workflow.")
    return 0


if __name__ == "__main__":
    # Ensure runtime singleton matches the store used after USE_FIRESTORE=false.
    raise SystemExit(asyncio.run(main()))
