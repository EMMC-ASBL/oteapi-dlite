"""A specialised strategy that finds a instances of a given datamodel
in the collection and give them new labels."""

## pylint: disable=unused-argument
from typing import TYPE_CHECKING, Annotated, Optional

from oteapi.models import AttrDict, FunctionConfig
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class DLiteRelabelConfig(AttrDict):
    """Configuration for relabel strategy."""

    datamodel: Annotated[
        str,
        Field(
            description="URI of datamodel who's instance should be relabeled.",
        ),
    ]
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
        labels = list(coll.get_subjects(p="_has-meta", o=config.datamodel))
        if not labels:
            raise ValueError(
                f"no instances to relabel of datamodel: {config.datamodel}"
            )
        if len(labels) > 1:
            raise ValueError(
                f"relabeling more than one instance is currently not supped: "
                f"{config.datamodel}"
            )
        label = labels[0]
        inst = coll.get(label)
        coll.remove(label)
        coll.add(config.newlabel, inst)

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)
