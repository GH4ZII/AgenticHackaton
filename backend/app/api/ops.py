"""Inventory and agent-action read APIs."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.serializers import inventory_to_dict
from app.runtime import get_store

router = APIRouter(prefix="/api", tags=["ops"])


@router.get("/inventory")
def list_inventory() -> dict:
    store = get_store()
    items = [inventory_to_dict(i) for i in store.list_inventory()]
    return {"inventory": items, "count": len(items)}


@router.get("/agent-actions")
def list_agent_actions() -> dict:
    store = get_store()
    actions = list(store.list_agent_actions())
    actions.sort(key=lambda a: a.get("timestamp") or "", reverse=True)
    return {"agent_actions": actions, "count": len(actions)}
