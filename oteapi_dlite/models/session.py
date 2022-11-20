"""Pydantic data models for DLite."""
from typing import Optional

from oteapi.models import SessionUpdate
from pydantic import Field


class DLiteSessionUpdate(SessionUpdate):
    """Class for returning values from DLite strategies."""

    collection_id: Optional[str] = Field(
        {},  # default_factory=new_collection,
        description="A reference to a DLite collection.",
    )
