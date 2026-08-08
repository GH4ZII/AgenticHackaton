"""Shared runtime store for agent tools (Phase 3/4)."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from app.seed import seed_if_empty, seed_store
from app.store.firestore_store import FirestoreStore

load_dotenv()

STORE: Any = None


def _use_firestore() -> bool:
    return os.getenv("USE_FIRESTORE", "").strip().upper() in {"1", "TRUE", "YES"}


def _build_store() -> Any:
    if _use_firestore():
        store = FirestoreStore()
        return seed_if_empty(store)
    return seed_store()


def get_store() -> Any:
    """Return the process-wide domain store."""
    global STORE
    if STORE is None:
        STORE = _build_store()
    return STORE


def reset_store() -> Any:
    """Rebuild the shared store.

    Memory mode: clear and re-seed.
    Firestore mode: keep existing documents; only seed if empty.
    """
    global STORE
    if _use_firestore():
        STORE = seed_if_empty(FirestoreStore())
    else:
        STORE = seed_store()
    return STORE
