"""Pydantic data models for DLite."""

from typing import Annotated, Optional

from oteapi.models.genericconfig import AttrDict
from pydantic import Field


class DLiteSessionUpdate(AttrDict):
    """Class for returning values from DLite strategies."""

    collection_id: Annotated[
        Optional[str], Field(description="A reference to a DLite collection.")
    ] = None
