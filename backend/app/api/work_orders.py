"""Work order read APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.serializers import work_order_to_dict
from app.runtime import get_store

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
