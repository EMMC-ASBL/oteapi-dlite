"""Generic function strategy using DLite storage plugin."""
# pylint: disable=unused-argument,invalid-name
import tempfile
from typing import TYPE_CHECKING, Optional

from oteapi.datacache import DataCache
from oteapi.models import (
    AttrDict,
    DataCacheConfig,
    FunctionConfig,
    SessionUpdate,
)
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, get_driver

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.interfaces import IFunctionStrategy


class AddInstanceConfig(AttrDict):
    """Configuration for adding an instance to the collection.
    """

    datamodel: str = Field(
        description='ID (URI or UUID) of the datamodel.',
    )
    value: dict = Field(
        description='Dict with instance values.',
    )
    label: str = Field(
        ...,
        description="Label of DLite instance to serialise in the collection.",
    )


class DLiteAddInstanceConfig(FunctionConfig):
    """DLite function strategy config."""

    configuration: AddInstanceConfig = Field(
        ..., description="Strategy-specific configuration for adding
        and instance to the collection."
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
        cacheconfig = config.datacache_config


        coll = get_collection(session)
        inst =  dlite.get_instance(config.datamodel)
        inst.from_dict(config.value)
        inst.label(config.label)

        coll.add(inst)
     
        return DLiteSessionUpdate(collection_id=coll.uuid)


# DLiteStorageConfig.update_forward_refs()
