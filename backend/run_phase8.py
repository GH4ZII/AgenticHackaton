"""Phase 8 success check: complete work order → verify → close incident."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")


def _check_env() -> int | None:
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().upper() in {
        "1",
        "TRUE",
        "YES",
    }
    if use_vertex:
        if not os.getenv("GOOGLE_CLOUD_PROJECT") or not os.getenv(
            "GOOGLE_CLOUD_LOCATION"
        ):
            print("Set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION.")
            return 1
        if os.getenv("GOOGLE_CLOUD_PROJECT", "").startswith("<"):
            print("Set a real GOOGLE_CLOUD_PROJECT in backend/.env")
            return 1
    elif not os.getenv("GOOGLE_API_KEY"):
        print("Set Vertex env or GOOGLE_API_KEY.")
        return 1
    return None


async def main() -> int:
    env_error = _check_env()
    if env_error is not None:
        return env_error

    os.environ["USE_FIRESTORE"] = "false"

    from app.api.demo import seed_demo_state
    from app.models.incident import IncidentStatus
    from app.models.machine import MachineStatus
    from app.models.work_order import WorkOrderStatus
    from app.runtime import get_store, reset_store
    from app.services.repair_workflow import complete_and_verify

    reset_store()
    seeded = seed_demo_state()
    store = get_store()

    work_orders = [
        w
        for w in store.list_work_orders()
        if w.status != WorkOrderStatus.COMPLETED
    ]
    if not work_orders:
        print("FAIL: demo seed did not create an open work order.")
        return 2

    work_order = work_orders[0]
    print(f"Demo incident: {seeded.get('incident_id')}")
    print(f"Completing work order: {work_order.work_order_id}")
    print("---")

    result = await complete_and_verify(store, work_order.work_order_id)
    print(result.message)
    print(f"Agent invoked: {result.agent_invoked}")
    if result.agent_result:
        print(f"Tools: {result.agent_result.tool_calls}")
        print("---")
        print(result.agent_result.final_text or "(no final text)")
        print("---")

    wo = store.get_work_order(work_order.work_order_id)
    machine = store.get_machine(work_order.machine_id)
    incident = result.incident

    if wo is None or wo.status != WorkOrderStatus.COMPLETED:
        print("FAIL: work order not COMPLETED.")
        return 3
    if incident is None or incident.status != IncidentStatus.RESOLVED:
        print(
            f"FAIL: incident not RESOLVED "
            f"(got {incident.status.value if incident else None})."
        )
        return 4
    if machine is None or machine.status != MachineStatus.HEALTHY:
        print(
            f"FAIL: machine not HEALTHY "
            f"(got {machine.status.value if machine else None})."
        )
        return 5

    print(
        f"WO={wo.work_order_id} COMPLETED | "
        f"incident={incident.incident_id} RESOLVED | "
        f"machine={machine.machine_id} HEALTHY"
    )
    print("\nSUCCESS: Closed loop — repair verified and incident closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
