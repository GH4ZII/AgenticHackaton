"""Inventory domain model."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    part_id: str
    name: str
    part_number: str
    stock: int = Field(ge=0)
    location: str
