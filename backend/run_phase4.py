"""Phase 4 success check: Firestore state survives a simulated restart."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")


def main() -> int:
    os.environ["USE_FIRESTORE"] = "true"

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if not project or project.startswith("<"):
        print("Set GOOGLE_CLOUD_PROJECT in backend/.env to your GCP project ID.")
        return 1

    from app.models.incident import Incident, IncidentStatus, Severity
    from app.models.work_order import WorkOrder, WorkOrderStatus
    from app.seed import seed_if_empty
    from app.services.firestore_service import get_firestore_client
    from app.store.firestore_store import FirestoreStore

    print(f"Project: {project}")
    print("Connecting to Firestore...")

    store_a = seed_if_empty(FirestoreStore(get_firestore_client(project)))
    machine = store_a.get_machine("PUMP-04")
    if machine is None:
        print("FAIL: PUMP-04 was not seeded into Firestore.")
        return 2
    print(f"Seeded/loaded machine: {machine.machine_id} status={machine.status.value}")

    incident_id = f"INC-P4-{uuid4().hex[:6].upper()}"
    work_order_id = f"WO-P4-{uuid4().hex[:6].upper()}"
    now = datetime.now(timezone.utc)

    store_a.add_incident(
        Incident(
            incident_id=incident_id,
            machine_id="PUMP-04",
            status=IncidentStatus.OPEN,
            severity=Severity.HIGH,
            detected_at=now,
            trigger_reason="Phase 4 persistence probe",
        )
    )
    store_a.upsert_work_order(
        WorkOrder(
            work_order_id=work_order_id,
            machine_id="PUMP-04",
            incident_id=incident_id,
            title="Phase 4 persistence probe",
            description="Created to verify Firestore survives restart.",
            suspected_failure="bearing degradation",
            priority="HIGH",
            recommended_action="Verify document still exists after new client",
            required_parts=["6205-2RS"],
            status=WorkOrderStatus.OPEN,
            created_at=now,
        )
    )
    store_a.add_agent_action(
        {
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "machine_id": "PUMP-04",
            "action": "phase4_probe",
            "detail": f"Wrote {incident_id} and {work_order_id}",
        }
    )

    print(f"Wrote incident {incident_id} and work order {work_order_id}")
    print("Simulating restart with a new Firestore client...")

    # New client + store instance = process restart without shared memory.
    store_b = FirestoreStore(get_firestore_client(project))
    loaded_machine = store_b.get_machine("PUMP-04")
    loaded_incident = store_b.get_incident(incident_id)
    loaded_wo = store_b.get_work_order(work_order_id)

    if loaded_machine is None:
        print("FAIL: machine missing after restart.")
        return 3
    if loaded_incident is None:
        print("FAIL: incident missing after restart.")
        return 4
    if loaded_wo is None:
        print("FAIL: work order missing after restart.")
        return 5

    print("After restart:")
    print(f"  machine:   {loaded_machine.machine_id} ({loaded_machine.status.value})")
    print(f"  incident:  {loaded_incident.incident_id} ({loaded_incident.status.value})")
    print(f"  work_order:{loaded_wo.work_order_id} ({loaded_wo.status.value})")
    print("\nSUCCESS: Restarting backend does not destroy application state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
