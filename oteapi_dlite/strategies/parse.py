"""Generic parse strategy using DLite storage plugin."""
# pylint: disable=unused-argument
from typing import TYPE_CHECKING, Dict, List, Optional, Union

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
from oteapi_dlite.utils import get_collection, get_driver, update_collection

if TYPE_CHECKING:
    from typing import Any


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
    global_configuration_additions: Dict[str, Union[str, List[str]]] = Field(
        {},
        description=(
            "A dictionary of DLite global configuration options to append. "
            "E.g., `storage_path` or `python_storage_plugin_path`."
        ),
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
        return SessionUpdate()

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            SessionUpdate instance.
        """
        if session is None:
            raise ValueError("Missing session")

        config = self.parse_config.configuration
        cacheconfig = config.datacache_config

        for (
            dlite_global_config,
            additions,
        ) in config.global_configuration_additions.items():
            if not hasattr(dlite, dlite_global_config):
                raise ValueError(
                    f"{dlite_global_config!r} is not a valid DLite global "
                    "configuration name."
                )
            if isinstance(additions, str):
                additions = [additions]
            getattr(dlite, dlite_global_config, []).extend(additions)

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
                key = session["key"]  # type: ignore
            else:
                raise ValueError(
                    "either `location` or `cacheconfig.accessKey` must be "
                    "provided"
                )

            cache = DataCache()
            with cache.getfile(key) as location:
                inst = dlite.Instance.from_location(
                    driver=driver,
                    location=str(location),
                    options=config.options,
                    id=config.id,
                )

        # Insert inst into collection
        coll = get_collection(session)
        coll.add(config.label, inst)

        # __TODO__
        # Can we savely assume that all strategies in a pipeline will be
        # executed in the same Python interpreter?  If not, we should write
        # the collection to a storage, such that it can be shared with the
        # other strategies.

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)


# DLiteParseConfig.update_forward_refs()
