"""Phase 2 success check: simulated telemetry can trigger an incident."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow `python run_phase2.py` from the backend directory.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.models.machine import MachineStatus
from app.models.telemetry import TelemetrySample
from app.seed import seed_store
from app.services.anomaly_detector import detect_anomaly


def main() -> int:
    store = seed_store()
    machine = store.get_machine("PUMP-04")
    assert machine is not None
    print(f"Seeded machine: {machine.machine_id} status={machine.status.value}")
    print(f"Seed telemetry samples: {len(store.get_telemetry_for_machine('PUMP-04'))}")
    print(f"Inventory parts: {len(store.list_inventory())}")

    # Healthy sample should NOT create an incident.
    healthy = TelemetrySample(
        machine_id="PUMP-04",
        timestamp=datetime(2026, 8, 7, 7, 0, tzinfo=timezone.utc),
        temperature_c=62.0,
        vibration_mm_s=3.0,
        motor_current_a=11.0,
    )
    healthy_result = detect_anomaly(store, healthy)
    print(
        f"\nHealthy sample -> anomalous={healthy_result.is_anomalous} "
        f"incidents={len(store.list_incidents())}"
    )
    if healthy_result.is_anomalous:
        print("FAIL: healthy telemetry should not trigger an incident.")
        return 1

    # Abnormal sample (demo climax values) SHOULD create an incident.
    abnormal = TelemetrySample(
        machine_id="PUMP-04",
        timestamp=datetime(2026, 8, 7, 12, 5, tzinfo=timezone.utc),
        temperature_c=86.0,
        vibration_mm_s=8.7,
        motor_current_a=14.0,
    )
    result = detect_anomaly(store, abnormal)
    print(f"\nAbnormal sample -> anomalous={result.is_anomalous}")
    for reason in result.reasons:
        print(f"  - {reason}")

    if not result.is_anomalous or result.incident is None:
        print("FAIL: abnormal telemetry did not create an incident.")
        return 1

    incident = result.incident
    machine = store.get_machine("PUMP-04")
    assert machine is not None

    print("\nIncident created:")
    print(f"  id:        {incident.incident_id}")
    print(f"  machine:   {incident.machine_id}")
    print(f"  status:    {incident.status.value}")
    print(f"  severity:  {incident.severity.value}")
    print(f"  reason:    {incident.trigger_reason}")
    print(f"  machine status now: {machine.status.value}")

    if machine.status != MachineStatus.WARNING:
        print("FAIL: machine status should be WARNING after anomaly.")
        return 1

    # Duplicate abnormal sample should reuse the open incident.
    duplicate = detect_anomaly(store, abnormal)
    if duplicate.incident is None or duplicate.incident.incident_id != incident.incident_id:
        print("FAIL: expected existing open incident to be reused.")
        return 1
    if len(store.list_incidents()) != 1:
        print("FAIL: duplicate incident was created.")
        return 1

    print("\nSUCCESS: Simulated telemetry triggered an incident.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
