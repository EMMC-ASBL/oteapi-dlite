"""DLite-specific data models."""

from __future__ import annotations

from typing import Annotated, Optional

from oteapi.models import AttrDict
from pydantic import Field, JsonValue


class DLiteResult(AttrDict):
    """Class for returning values from DLite strategies."""

    collection_id: Annotated[
        Optional[str], Field(description="A reference to a DLite collection.")
    ] = None


class DLiteConfiguration(DLiteResult):
    """Data model representing recurring fields necessary in strategy-specific
    configurations for DLite strategies.

    Note, this data model already includes the `collection_id` field from the
    `DLiteResult` data model.
    """

    dlite_settings: Annotated[
        dict[str, JsonValue],
        Field(
            description=(
                "Settings used by DLite strategies within a single pipeline "
                "run."
            )
        ),
    ] = {}  # noqa: RUF012
