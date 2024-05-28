"""A specialised strategy that finds a instances of a given datamodel
in the collection and give them new labels."""

# pylint: disable=unused-argument
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Optional

import dlite
from oteapi.datacache import DataCache
from oteapi.models import AttrDict, DataCacheConfig, FunctionConfig
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, get_driver, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class DLiteRelabelConfig(AttrDict):
    """Configuration for relabel strategy."""

    datamodel: Annotated[
        str,
        Field(
            description="URI of datamodel who's instance should be relabeled.",
        ),
    ] = None
    newlabel: Annotated[
        str,
        Field(
            description="Label of the new DLite instance in the collection.",
        ),
    ]


class DLiteRelabelFunctionConfig(FunctionConfig):
    """DLite relabel function strategy config."""

    configuration: Annotated[
        DLiteRelabelConfig,
        Field(description="DLite relabel strategy-specific configuration."),
    ]


@dataclass
class DLiteRelabelStrategy:
    """DLite relabel strategy for relabeling instances in the collection.

    **Registers strategies**:

    - `("mediaType", "application/vnd.dlite-relabel")`

    """

    function_config: DLiteRelabelFunctionConfig

    def initialize(
        self,
        session: Optional[dict[str, "Any"]] = None,
    ) -> DLiteSessionUpdate:
        """Initialize."""
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)

    def get(
        self, session: Optional[dict[str, "Any"]] = None
    ) -> DLiteSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            SessionUpdate instance.
        """
        config = self.function_config.configuration

        coll = get_collection(session)

        print("***", list(coll.get_labels()))
        # instanses =

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)
