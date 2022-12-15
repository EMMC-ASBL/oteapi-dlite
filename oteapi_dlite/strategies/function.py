"""Generic function strategy using DLite storage plugin."""
# pylint: disable=unused-argument,invalid-name
import tempfile
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import dlite
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
from oteapi_dlite.utils import get_collection, get_driver, update_collection

if TYPE_CHECKING:
    from typing import Any


class DLiteStorageConfig(AttrDict):
    """Configuration for a generic DLite storage filter.

    The DLite storage driver to can be specified using either the `driver`
    or `mediaType` field.

    Where the output should be written, is specified using either the
    `location` or `datacache_config.accessKey` field.
    """

    driver: Optional[str] = Field(
        None,
        description='Name of DLite driver (ex: "json").',
    )
    mediaType: Optional[str] = Field(
        None,
        description='Media type for DLite driver (ex: "application/json").',
    )
    location: Optional[str] = Field(
        None,
        description=(
            "Location of storage to write to.  If unset to store in data "
            "cache using the key provided with `datacache_config.accessKey` "
            "(defaults to 'function_data')."
        ),
    )
    options: Optional[str] = Field(
        None,
        description=(
            "Comma-separated list of options passed to the DLite "
            "storage plugin."
        ),
    )
    label: str = Field(
        ...,
        description="Label of DLite instance to serialise in the collection.",
    )
    collection_id: Optional[str] = Field(
        None,
        description=("ID of the collection to use."),
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


class DLiteFunctionConfig(FunctionConfig):
    """DLite function strategy config."""

    configuration: DLiteStorageConfig = Field(
        ..., description="DLite function strategy-specific configuration."
    )


@dataclass
class DLiteFunctionStrategy:
    """Generic DLite function strategy utilising DLite storage plugins.

    **Registers strategies**:

    - `("mediaType", "application/vnd.dlite-generate")`

    """

    function_config: DLiteFunctionConfig

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
        if session is None:
            raise ValueError("Missing session")

        config = self.function_config.configuration
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
                mediaType=config.mediaType,
            )
        )

        if config.collection_id:
            coll = dlite.get_instance(config.collection_id)
        else:
            coll = get_collection(session)
        inst = coll[config.label]

        # Save instance
        if config.location:
            inst.save(driver, config.location, config.options)
        else:
            if cacheconfig and cacheconfig.accessKey:
                key = cacheconfig.accessKey
            elif "key" in session:  # type: ignore
                key = "function_data"

            cache = DataCache()
            with tempfile.TemporaryDirectory() as tmpdir:
                inst.save(driver, "{tmpdir}/data", config.options)
                with open(f"{tmpdir}/data", "rb") as f:
                    cache.add(f.read(), key=key)

        # __TODO__
        # Can we savely assume that all strategies in a pipeline will be
        # executed in the same Python interpreter?  If not, we should write
        # the collection to a storage, such that it can be shared with the
        # other strategies.

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)


# DLiteStorageConfig.update_forward_refs()
