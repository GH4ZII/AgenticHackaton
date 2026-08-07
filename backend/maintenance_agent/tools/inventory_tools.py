"""Inventory tools backed by the in-memory domain store."""

from __future__ import annotations

from app.runtime import get_store


def check_inventory(part_query: str) -> dict:
    """Search spare-parts inventory by name or part number.

    Use this before creating a work order to confirm whether required
    parts such as bearings are in stock.

    Args:
        part_query: Search text, for example "bearing" or "6205-2RS".

    Returns:
        Matching inventory items with stock levels.
    """
    store = get_store()
    matches = store.search_inventory(part_query)
    return {
        "status": "success",
        "query": part_query,
        "matches": [
            {
                "part_id": item.part_id,
                "name": item.name,
                "part_number": item.part_number,
                "stock": item.stock,
                "location": item.location,
            }
            for item in matches
        ],
        "match_count": len(matches),
    }
