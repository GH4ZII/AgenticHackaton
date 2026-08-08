"""Domain models for the Maintenance Agent."""

from app.models.approval import ApprovalRequest, ApprovalStatus
from app.models.incident import Incident, IncidentStatus, Severity
from app.models.inventory import InventoryItem
from app.models.machine import Machine, MachineStatus
from app.models.telemetry import TelemetrySample
from app.models.work_order import WorkOrder, WorkOrderStatus

__all__ = [
    "ApprovalRequest",
    "ApprovalStatus",
    "Incident",
    "IncidentStatus",
    "InventoryItem",
    "Machine",
    "MachineStatus",
    "Severity",
    "TelemetrySample",
    "WorkOrder",
    "WorkOrderStatus",
]
