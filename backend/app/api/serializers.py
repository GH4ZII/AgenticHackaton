"""Shared API serialization helpers."""

from __future__ import annotations

from typing import Any


def machine_to_dict(machine: Any) -> dict[str, Any]:
    return machine.model_dump(mode="json")


def incident_to_dict(incident: Any) -> dict[str, Any]:
    return incident.model_dump(mode="json")


def work_order_to_dict(work_order: Any) -> dict[str, Any]:
    return work_order.model_dump(mode="json")


def telemetry_to_dict(sample: Any) -> dict[str, Any]:
    return sample.model_dump(mode="json")


def inventory_to_dict(item: Any) -> dict[str, Any]:
    return item.model_dump(mode="json")
