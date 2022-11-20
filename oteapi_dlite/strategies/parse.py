"""Generic parse strategy using DLite storage plugin."""
# pylint: disable=unused-argument
from typing import TYPE_CHECKING, Optional

import dlite
from oteapi.datacache import DataCache
from oteapi.models import (
    AttrDict,
    DataCacheConfig,
    ResourceConfig,
    SessionUpdate,
)
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_driver, init_session

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.interfaces import IParseStrategy


class DLiteParseConfig(AttrDict):
    """Configuration for generic DLite parser."""

    driver: Optional[str] = Field(
        None,
        description='Name of DLite driver (ex: "json").',
    )
    location: Optional[str] = Field(
        None,
        description=(
            "Explicit location of storage.  Normally data is read from the "
            "data cache using `datacache_config.accessKey` (default: 'key')."
        ),
    )
    options: Optional[str] = Field(
        None,
        description=(
            "Comma-separated list of options passed to the DLite storage "
            "plugin."
        ),
    )
    id: Optional[str] = Field(
        None,
        description="If given, the id of the instance in the storage.",
    )
    label: str = Field(
        ...,
        description="Label of the new DLite instance in the collection.",
    )
    datacache_config: Optional[DataCacheConfig] = Field(
        None,
        description="Configuration options for the local data cache.",
    )


class DLiteParseResourceConfig(ResourceConfig):
    """DLite parse strategy resource config."""

    configuration: DLiteParseConfig = Field(
        ..., description="DLite parse strategy-specific configuration."
    )


@dataclass
class DLiteParseStrategy:
    """Generic DLite parse strategy utilising DLite storage plugins.

    **Registers strategies**:

    - `("mediaType", "application/vnd.dlite-parse")`

    """

    parse_config: DLiteParseResourceConfig

    def initialize(
        self,
        session: "Optional[Dict[str, Any]]" = None,
    ) -> "SessionUpdate":
        """Initialize."""
        init_session(session)
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
        init_session(session)

        config = self.parse_config.configuration
        cacheconfig = config.datacache_config

        driver = (
            config.driver
            if config.driver
            else get_driver(
                mediaType=self.parse_config.mediaType,
            )
        )

        # Create instance
        if config.location:
            inst = dlite.Instance.from_location(
                driver=driver,
                location=config.location,
                options=config.options,
                id=config.id,
            )
        else:
            if cacheconfig and cacheconfig.accessKey:
                key = cacheconfig.accessKey
            elif "key" in session:  # type: ignore
                key = session.key  # type: ignore
            else:
                raise ValueError(
                    "either `location` or `cacheconfig.accessKey` must be "
                    "provided"
                )

            cache = DataCache()
            with cache.getfile(key) as location:
                inst = dlite.Instance.from_location(
                    driver=driver,
                    location=location,
                    options=config.options,
                    id=config.id,
                )

        # Insert inst into collection
        coll: dlite.Collection = dlite.get_instance(
            session["collection_id"]  # type:ignore
        )
        coll.add(config.label, inst)

        return DLiteSessionUpdate(collection_id=coll.uuid)


DLiteParseConfig.update_forward_refs()
