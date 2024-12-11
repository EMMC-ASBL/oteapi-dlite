"""Generic parse strategy using DLite storage plugin."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Optional

if sys.version_info >= (3, 9, 1):
    from typing import Literal
else:
    from typing_extensions import Literal  # type: ignore[assignment]

import dlite
from oteapi.datacache import DataCache
from oteapi.models import (
    AttrDict,
    DataCacheConfig,
    HostlessAnyUrl,
    ParserConfig,
    ResourceConfig,
)
from oteapi.plugins import create_strategy
from pydantic import AnyHttpUrl, Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteResult
from oteapi_dlite.utils import get_collection, get_driver, update_collection


class DLiteParseConfig(DLiteResult):
    """Configuration for generic DLite parser."""

    # "Required" resource strategy fields
    downloadUrl: Annotated[
        Optional[HostlessAnyUrl],
        Field(
            description=ResourceConfig.model_fields["downloadUrl"].description
        ),
    ] = None

    mediaType: Annotated[
        Optional[str],
        Field(description=ResourceConfig.model_fields["mediaType"].description),
    ] = None

    # Parser-specific configuration
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
    download_config: Annotated[
        AttrDict,
        Field(description="Configurations provided to a download strategy."),
    ] = AttrDict()
    datacache_config: Annotated[
        Optional[DataCacheConfig],
        Field(
            description="Configuration options for the local data cache.",
        ),
    ] = None


class DLiteParseParserConfig(ParserConfig):
    """DLite parse strategy resource config."""

    parserType: Annotated[
        Literal["application/vnd.dlite-parse"],
        Field(description=ParserConfig.model_fields["parserType"].description),
    ]
    configuration: Annotated[
        DLiteParseConfig,
        Field(description="DLite parse strategy-specific configuration."),
    ]
    entity: Annotated[
        Optional[AnyHttpUrl],
        Field(description=ParserConfig.model_fields["entity"].description),
    ] = None


@dataclass
class DLiteParseStrategy:
    """Generic DLite parse strategy utilising DLite storage plugins.

    **Registers strategies**:

    - `("mediaType", "application/vnd.dlite-parse")`

    """

    parse_config: DLiteParseParserConfig

    def initialize(self) -> DLiteResult:
        """Initialize."""
        return DLiteResult(
            collection_id=get_collection(
                self.parse_config.configuration.collection_id
            ).uuid
        )

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
            # Download the file
            download_config = config.model_dump()
            download_config["configuration"] = (
                config.download_config.model_dump()
            )
            output = create_strategy("download", download_config).get()

            if cacheconfig and cacheconfig.accessKey:
                key = cacheconfig.accessKey
            elif "key" in output:
                key = output["key"]
            else:
                raise RuntimeError(
                    "No data cache key provided for the downloaded content."
                )

            # See if we can extract file suffix from downloadUrl
            if config.downloadUrl:
                suffix = Path(str(config.downloadUrl)).suffix
            else:
                suffix = None

            cache = DataCache(config.datacache_config)
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
