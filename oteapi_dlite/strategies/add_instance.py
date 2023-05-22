"""Generic function strategy using DLite storage plugin."""
# pylint: disable=unused-argument,invalid-name
from typing import TYPE_CHECKING, Optional

import dlite
from dlite.utils import infer_dimensions
from oteapi.models import AttrDict, FunctionConfig, SessionUpdate
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.interfaces import IFunctionStrategy


class AddInstanceConfig(AttrDict):
    """Configuration for adding an instance to the collection."""

    datamodel: str = Field(
        description="ID (URI or UUID) of the datamodel.",
    )
    property_values: dict = Field(
        description="Dict with property values.",
    )
    dimensions: "Optional[dict]" = Field(
        None,
        description="Dict with dimension values.  If not provided, the "
        "dimensions will be inferred from `values`.",
    )
    label: str = Field(
        ...,
        description="Label of DLite instance to serialise in the collection.",
    )


class DLiteAddInstanceConfig(FunctionConfig):
    """DLite function strategy config."""

    configuration: AddInstanceConfig = Field(
        ...,
        description="Strategy-specific configuration for adding "
        "an instance to the collection.",
    )


@dataclass
class DLiteAddInstanceStrategy:
    """DLite function strategy to add an Instance to the collection.

    **Registers strategies**:

    - `("mediaType", "application/vnd.dlite-addinstance")`

    """

    function_config: DLiteAddInstanceConfig

    def initialize(
        self,
        session: "Optional[Dict[str, Any]]" = None,
    ) -> "SessionUpdate":
        """Initialize."""
        return SessionUpdate()

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "DLiteSessionUpdate":
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
        datamodel = dlite.get_instance(config.datamodel)
        if config.dimensions is None:
            dims = infer_dimensions(
                datamodel, config.property_values, strict=True
            )
        else:
            dims = config.dimensions
        inst = datamodel(dimensions=dims, properties=config.values)

        coll.add(label=config.label, inst=inst)

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)
