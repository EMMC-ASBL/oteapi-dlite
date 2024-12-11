"""Filter for serialisation using DLite."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Optional

import dlite
from oteapi.models import FilterConfig
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteResult
from oteapi_dlite.utils import get_collection, update_collection


class SerialiseConfig(DLiteResult):
    """DLite serialise-specific configurations."""

    driver: Annotated[
        str,
        Field(
            description="Name of DLite plugin used for serialisation.",
        ),
    ]
    location: Annotated[
        Path,
        Field(
            description="Path or URL to serialise to.",
        ),
    ]
    options: Annotated[
        Optional[str],
        Field(
            description="Options passed to the driver.",
        ),
    ] = ""
    labels: Annotated[
        Optional[Sequence[str]],
        Field(
            None,
            description=(
                "Optional sequence of labels in the collection to serialise.  "
                "The default is to serialise the entire collection."
            ),
        ),
    ] = None


class SerialiseFilterConfig(FilterConfig):
    """Filter config for serialise."""

    configuration: Annotated[
        SerialiseConfig,
        Field(
            description="Serialise-specific configurations.",
        ),
    ]


@dataclass
class SerialiseStrategy:
    """Filter for serialisation using DLite.

    **Registers strategies**:

    - `("filterType", "dlite_serialise")`

    """

    filter_config: SerialiseFilterConfig

    def initialize(self) -> DLiteResult:
        """Initialize."""
        return DLiteResult(
            collection_id=get_collection(
                self.filter_config.configuration.collection_id
            ).uuid
        )

    def get(self) -> DLiteResult:
        """Execute the strategy."""
        config = self.filter_config.configuration

        coll = get_collection(config.collection_id)

        storage = dlite.Storage(
            driver_or_url=config.driver,
            location=str(config.location),
            options=config.options,
        )
        if config.labels is None:
            coll.save_to_storage(storage)
        else:
            for label in config.labels:
                inst = coll.get(label)
                inst.save_to_storage(storage)

        update_collection(coll)
        return DLiteResult(collection_id=coll.uuid)
