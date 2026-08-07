"""Firestore client helpers for Phase 4."""

from __future__ import annotations

import os

from google.cloud import firestore


def get_firestore_client(project_id: str | None = None) -> firestore.Client:
    """Create a Firestore client using Application Default Credentials."""
    project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project or project.startswith("<"):
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT must be set to a real GCP project ID "
            "when USE_FIRESTORE=true."
        )
    return firestore.Client(project=project)
