"""Generic parse strategy using DLite storage plugin."""

# pylint: disable=unused-argument
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Optional

import dlite
from oteapi.datacache import DataCache
from oteapi.models import AttrDict, DataCacheConfig, ResourceConfig
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, get_driver, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class DLiteParseConfig(AttrDict):
    """Configuration for generic DLite parser."""

    driver: Annotated[
        Optional[str],
        Field(
            description='Name of DLite driver (ex: "json").',
        ),
    ] = None
    collection_id: Annotated[
        Optional[str], Field(description="A reference to a DLite collection.")
    ] = None
    location: Annotated[
        Optional[str],
        Field(
            description=(
                "Explicit location of storage.  Normally data is read from the "
                "data cache using `datacache_config.accessKey` (default: "
                "'key')."
            ),
        ),
    ] = None
    options: Annotated[
        Optional[str],
        Field(
            description=(
                "Comma-separated list of options passed to the DLite storage "
                "plugin."
            ),
        ),
    ] = None
    id: Annotated[
        Optional[str],
        Field(
            description="If given, the id of the instance in the storage.",
        ),
    ] = None
    label: Annotated[
        str,
        Field(
            description="Label of the new DLite instance in the collection.",
        ),
    ]
    datacache_config: Annotated[
        Optional[DataCacheConfig],
        Field(
            description="Configuration options for the local data cache.",
        ),
    ] = None


class DLiteParseResourceConfig(ResourceConfig):
    """DLite parse strategy resource config."""

    configuration: Annotated[
        DLiteParseConfig,
        Field(description="DLite parse strategy-specific configuration."),
    ]


@dataclass
class DLiteParseStrategy:
    """Generic DLite parse strategy utilising DLite storage plugins.

    **Registers strategies**:

    - `("mediaType", "application/vnd.dlite-parse")`

    """

    parse_config: DLiteParseResourceConfig

    def initialize(self) -> DLiteSessionUpdate:
        """Initialize."""
        collection_id = (
            self.parse_config.configuration.collection_id
            or get_collection().uuid
        )
        return DLiteSessionUpdate(collection_id=collection_id)

    def get(self) -> DLiteSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            SessionUpdate instance.
        """
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
            else:
                raise ValueError(
                    "either `location` or `datacache_config.accessKey` must be "
                    "provided"
                )

            # See if we can extract file suffix from downloadUrl
            if self.parse_config.downloadUrl:
                suffix = Path(str(self.parse_config.downloadUrl)).suffix
            else:
                suffix = None

            cache = DataCache()
            with cache.getfile(key, suffix=suffix) as location:
                inst = dlite.Instance.from_location(
                    driver=driver,
                    location=str(location),
                    options=config.options,
                    id=config.id,
                )

        # Insert inst into collection
        coll = get_collection(
            collection_id=self.parse_config.configuration.collection_id
        )
        coll.add(config.label, inst)

        # __TODO__
        # See
        # https://github.com/EMMC-ASBL/oteapi-dlite/pull/84#discussion_r1050437185
        # and following comments.
        #
        # Since we cannot safely assume that all strategies in a
        # pipeline will be executed in the same Python interpreter,
        # the collection should be written to a storage, such that it
        # can be shared with the other strategies.

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)
