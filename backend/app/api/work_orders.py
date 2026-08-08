"""Work order read/complete APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.serializers import incident_to_dict, work_order_to_dict
from app.runtime import get_store
from app.services.repair_workflow import complete_and_verify

router = APIRouter(prefix="/api", tags=["work_orders"])


@router.get("/work-orders")
def list_work_orders() -> dict:
    store = get_store()
    orders = [work_order_to_dict(w) for w in store.list_work_orders()]
    orders.sort(key=lambda w: w.get("created_at") or "", reverse=True)
    return {"work_orders": orders, "count": len(orders)}


@router.get("/work-orders/{work_order_id}")
def get_work_order(work_order_id: str) -> dict:
    store = get_store()
    order = store.get_work_order(work_order_id)
    if order is None:
        raise HTTPException(
            status_code=404, detail=f"Work order '{work_order_id}' not found"
        )
    return {"work_order": work_order_to_dict(order)}


@router.post("/work-orders/{work_order_id}/complete")
async def complete_work_order(work_order_id: str) -> dict:
    """Mark work order completed, inject healthy telemetry, verify with agent."""
    store = get_store()
    try:
        result = await complete_and_verify(store, work_order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "status": "ok",
        "message": result.message,
        "already_completed": result.already_completed,
        "agent_invoked": result.agent_invoked,
        "machine_status": result.machine_status,
        "work_order": work_order_to_dict(result.work_order),
        "incident": (
            incident_to_dict(result.incident) if result.incident is not None else None
        ),
        "tools_called": (
            result.agent_result.tool_calls if result.agent_result else []
        ),
        "agent_summary": (
            result.agent_result.final_text if result.agent_result else None
        ),
    }
