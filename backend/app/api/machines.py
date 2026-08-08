"""Machine and telemetry read APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.serializers import machine_to_dict, telemetry_to_dict
from app.models.machine import MachineStatus
from app.runtime import get_store

router = APIRouter(prefix="/api", tags=["machines"])


def _list_machines(store):
    if hasattr(store, "machines") and isinstance(store.machines, dict):
        return list(store.machines.values())
    # Firestore: stream collection
    if hasattr(store, "client"):
        from app.models.machine import Machine

        return [
            Machine.model_validate(doc.to_dict())
            for doc in store.client.collection("machines").stream()
        ]
    return []


@router.get("/machines")
def list_machines() -> dict:
    store = get_store()
    machines = [machine_to_dict(m) for m in _list_machines(store)]
    machines.sort(key=lambda m: m["machine_id"])
    return {"machines": machines, "count": len(machines)}


@router.get("/machines/{machine_id}")
def get_machine(machine_id: str) -> dict:
    store = get_store()
    machine = store.get_machine(machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")
    open_incident = store.get_open_incident_for_machine(machine_id)
    return {
        "machine": machine_to_dict(machine),
        "open_incident_id": open_incident.incident_id if open_incident else None,
        "maintenance_history": store.get_maintenance_history(machine_id),
    }


@router.get("/machines/{machine_id}/telemetry")
def get_machine_telemetry(machine_id: str) -> dict:
    store = get_store()
    machine = store.get_machine(machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")
    samples = store.get_telemetry_for_machine(machine_id)
    return {
        "machine_id": machine_id.strip().upper(),
        "samples": [telemetry_to_dict(s) for s in samples],
        "limits": {
            "temperature_c": machine.temperature_limit,
            "vibration_mm_s": machine.vibration_limit,
            "motor_current_a": machine.motor_current_limit,
        },
    }


@router.get("/dashboard")
def dashboard_summary() -> dict:
    store = get_store()
    machines = _list_machines(store)
    incidents = store.list_incidents()
    work_orders = store.list_work_orders()

    healthy = sum(1 for m in machines if m.status == MachineStatus.HEALTHY)
    warning = sum(
        1
        for m in machines
        if m.status
        in {
            MachineStatus.WARNING,
            MachineStatus.MONITORING,
            MachineStatus.MAINTENANCE_REQUIRED,
            MachineStatus.OUT_OF_SERVICE,
        }
    )
    open_incidents = sum(1 for i in incidents if i.status.value != "RESOLVED")
    open_work_orders = sum(1 for w in work_orders if w.status.value != "COMPLETED")

    return {
        "total_machines": len(machines),
        "healthy_machines": healthy,
        "attention_machines": warning,
        "open_incidents": open_incidents,
        "active_work_orders": open_work_orders,
    }
