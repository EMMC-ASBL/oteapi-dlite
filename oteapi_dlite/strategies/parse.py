"""Generic parse strategy using DLite storage plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import dlite
from oteapi.datacache import DataCache
from oteapi.models import DataCacheConfig, HostlessAnyUrl, ParserConfig, ResourceConfig
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteResult
from oteapi_dlite.utils import get_collection, get_driver, update_collection


class DLiteParseConfig(DLiteResult):
    """Configuration for generic DLite parser."""

    # From a download strategy
    key: Annotated[
        Optional[str], Field(description="Cache key to a downloaded source.")
    ] = None

    # "Required" resource strategy fields
    downloadUrl: Annotated[
        Optional[HostlessAnyUrl],
        Field(description=ResourceConfig.model_fields["downloadUrl"].description),
    ] = None
    mediaType: Annotated[
        Optional[str],
        Field(description=ResourceConfig.model_fields["mediaType"].description),
    ] = None

    driver: Annotated[
        str,
        Field(
            description='Name of DLite driver (ex: "json").',
        ),
    ]
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
        Optional[str],
        Field(
            description=(
                "Optional label of the new DLite instance in the collection."
            ),
        ),
    ] = None
    datamodel: Annotated[
        Optional[str],
        Field(
            description=(
                "DLite datamodel documenting the structure of the data set. "
                "Often unused, since the datamodel is implicitly defined in "
                "the DLite driver (DLite plugin), but for a documentation "
                "point of view this is a very important field."
            ),
        ),
    ] = None
    datacache_config: Annotated[
        Optional[DataCacheConfig],
        Field(
            description="Configuration options for the local data cache.",
        ),
    ] = None


class DLiteParseResourceConfig(ParserConfig):
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

    def initialize(self) -> DLiteResult:
        """Initialize."""
        return DLiteResult(collection_id=get_collection(self.parse_config.configuration.collection_id).uuid)

    def get(self) -> DLiteResult:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Returns:
            Reference to a DLite collection ID.

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
            elif config.key:
                key = config.key
            else:
                raise ValueError(
                    "either `location` or `datacache_config.accessKey` must be "
                    "provided"
                )

            # See if we can extract file suffix from downloadUrl
            if config.downloadUrl:
                suffix = Path(str(config.downloadUrl)).suffix
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
        coll = get_collection(config.collection_id)
        label = config.label if config.label else inst.uuid
        coll.add(label, inst)

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
        return DLiteResult(collection_id=coll.uuid)
