"""Pydantic data models for DLite."""

from typing import Annotated, Optional

from oteapi.models import SessionUpdate
from pydantic import Field


class DLiteSessionUpdate(SessionUpdate):
    """Class for returning values from DLite strategies."""

    collection_id: Annotated[
        Optional[str], Field(description="A reference to a DLite collection.")
    ] = None
