"""Phase 9 success check: CRITICAL shutdown requires human approval."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")


def main() -> int:
    os.environ["USE_FIRESTORE"] = "false"

    from app.api.approvals import approve_shutdown, reject_shutdown
    from app.api.demo import seed_critical_demo
    from app.models.approval import ApprovalStatus
    from app.models.machine import MachineStatus
    from app.runtime import get_store, reset_store
    from maintenance_agent.tools.approval_tools import request_shutdown_approval

    reset_store()

    # --- Path A: reject keeps machine in maintenance ---
    seeded = seed_critical_demo()
    store = get_store()
    reject_id = seeded["approval_id"]
    print(f"Seeded CRITICAL approval (reject path): {reject_id}")
    print(f"Machine status before reject: {seeded['machine_status']}")
    print(f"shutdown_executed on seed: {seeded['shutdown_executed']}")

    if seeded["shutdown_executed"]:
        print("FAIL: seed-critical must not execute shutdown.")
        return 1

    machine = store.get_machine("PUMP-04")
    if machine is None or machine.status != MachineStatus.MAINTENANCE_REQUIRED:
        print("FAIL: seed should leave machine MAINTENANCE_REQUIRED.")
        return 2
    if machine.status == MachineStatus.OUT_OF_SERVICE:
        print("FAIL: machine must not be OUT_OF_SERVICE before approval.")
        return 3

    rejected = reject_shutdown(reject_id)
    store = get_store()
    approval = store.get_approval(reject_id)
    machine = store.get_machine("PUMP-04")
    print(f"Reject result: {rejected['message']}")

    if approval is None or approval.status != ApprovalStatus.REJECTED:
        print("FAIL: approval not REJECTED after reject.")
        return 4
    if machine is None or machine.status != MachineStatus.MAINTENANCE_REQUIRED:
        print(
            f"FAIL: after reject expected MAINTENANCE_REQUIRED, "
            f"got {machine.status.value if machine else None}."
        )
        return 5
    if machine.status == MachineStatus.OUT_OF_SERVICE:
        print("FAIL: reject must not set OUT_OF_SERVICE.")
        return 6

    print("Reject path OK — machine stayed MAINTENANCE_REQUIRED.")
    print("---")

    # --- Path B: approve sets OUT_OF_SERVICE ---
    seeded2 = seed_critical_demo()
    approve_id = seeded2["approval_id"]
    print(f"Seeded CRITICAL approval (approve path): {approve_id}")

    machine = store.get_machine("PUMP-04")
    if machine is None or machine.status == MachineStatus.OUT_OF_SERVICE:
        print("FAIL: approve-path seed must not leave machine OUT_OF_SERVICE.")
        return 7

    # Tool path also creates PENDING without shutting down.
    tool_result = request_shutdown_approval(
        machine_id="PUMP-04",
        incident_id=seeded2["incident_id"],
        reason="Duplicate tool call should reuse pending approval.",
    )
    if tool_result.get("shutdown_executed") is not False:
        print("FAIL: request_shutdown_approval must set shutdown_executed=false.")
        return 8
    print(f"Tool reuse: {tool_result.get('message')}")

    approved = approve_shutdown(approve_id)
    store = get_store()
    approval = store.get_approval(approve_id)
    machine = store.get_machine("PUMP-04")
    print(f"Approve result: {approved['message']}")

    if approval is None or approval.status != ApprovalStatus.APPROVED:
        print("FAIL: approval not APPROVED after approve.")
        return 9
    if machine is None or machine.status != MachineStatus.OUT_OF_SERVICE:
        print(
            f"FAIL: after approve expected OUT_OF_SERVICE, "
            f"got {machine.status.value if machine else None}."
        )
        return 10

    print(
        f"Approve path OK — {machine.machine_id} = OUT_OF_SERVICE "
        f"(approval {approve_id})."
    )
    print("\nSUCCESS: Human approval required before OUT_OF_SERVICE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
