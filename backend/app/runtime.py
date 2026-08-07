"""Shared runtime store for agent tools (Phase 3)."""

from __future__ import annotations

from app.seed import seed_store
from app.store.memory_store import MemoryStore

STORE: MemoryStore = seed_store()


def get_store() -> MemoryStore:
    """Return the process-wide in-memory store."""
    return STORE


def reset_store() -> MemoryStore:
    """Re-seed the shared store (useful for tests / phase scripts)."""
    global STORE
    STORE = seed_store()
    return STORE
