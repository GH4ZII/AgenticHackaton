"""Machine manual search tools backed by the in-memory domain store."""

from __future__ import annotations

from app.runtime import get_store


def search_machine_manual(machine_id: str, query: str) -> dict:
    """Search simulated machine manual sections for relevant guidance.

    Use this to look up failure symptoms, vibration limits, recommended
    parts, or safety policy for the machine under investigation.

    Args:
        machine_id: Machine identifier, for example "PUMP-04".
        query: Search text, for example "bearing vibration" or "shutdown".

    Returns:
        Matching manual sections, or a not-found / empty result payload.
    """
    store = get_store()
    machine = store.get_machine(machine_id)
    if machine is None and machine_id.strip().upper() not in store.manuals:
        return {
            "status": "not_found",
            "machine_id": machine_id,
            "message": f"No manual found for '{machine_id}'.",
        }

    matches = store.search_manual(machine_id, query)
    return {
        "status": "success",
        "machine_id": machine_id.strip().upper(),
        "query": query,
        "matches": matches,
        "match_count": len(matches),
    }
