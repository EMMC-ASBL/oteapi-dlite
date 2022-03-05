"""Filter for serialisation using DLite."""
# pylint: disable=no-self-use
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Sequence

import dlite
from oteapi.models import AttrDict, FilterConfig
from pydantic import Field

from oteapi_dlite.models import DLiteSessionUpdate

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict


class SerialiseConfig(AttrDict):
    """DLite serialise-specific configurations."""

    driver: str = Field(
        ...,
        description="Name of DLite plugin used for serialisation.",
    )
    location: Path = Field(
        ...,
        description="Path or URL to serialise to.",
    )
    options: Optional[str] = Field(
        "",
        description="Options passed to the driver.",
    )
    labels: Optional[Sequence[str]] = Field(
        None,
        description=(
            "Optional sequence of labels in the collection to serialise.  "
            "The default is to serialise the entire collection."
        ),
    )


class SerialiseFilterConfig(FilterConfig):
    """Filter config for serialise."""

    configuration: SerialiseConfig = Field(
        ...,
        description="Serialise-specific configurations.",
    )


@dataclass
class SerialiseStrategy:
    """Filter for serialisation using DLite.

    **Registers strategies**:

    - `("filterType", "dlite_serialise")`

    """

    filter_config: "SerialiseFilterConfig"

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Initialize."""
        if session is None:
            raise ValueError("Missing session")
        return DLiteSessionUpdate(collection_id=session["collection_id"])

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> DLiteSessionUpdate:
        """Execute the strategy."""
        if session is None:
            raise ValueError("Missing session")

        config = self.filter_config.configuration

        coll = dlite.get_collection(session["collection_id"])

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

        return DLiteSessionUpdate(collection_id=session["collection_id"])
