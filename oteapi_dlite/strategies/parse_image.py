"""Strategy class for parsing an image to a DLite instance."""

from __future__ import annotations

import logging
import sys
from typing import Annotated, Optional

if sys.version_info >= (3, 9, 1):
    from typing import Literal
else:
    from typing_extensions import Literal  # type: ignore[assignment]

import numpy as np
from oteapi.datacache import DataCache
from oteapi.models import ParserConfig, ResourceConfig
from oteapi.plugins import create_strategy
from oteapi.strategies.parse.image import ImageConfig
from PIL import Image
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteResult
from oteapi_dlite.utils import get_collection, get_meta, update_collection

LOGGER = logging.getLogger("oteapi_dlite.strategies")
LOGGER.setLevel(logging.DEBUG)


class DLiteImageConfig(ImageConfig, DLiteResult):
    """Configuration for DLite image parser."""

    # Resource config
    mediaType: Annotated[
        Optional[
            Literal[
                "image/vnd.dlite-jpg",
                "image/vnd.dlite-jpeg",
                "image/vnd.dlite-jp2",
                "image/vnd.dlite-png",
                "image/vnd.dlite-gif",
                "image/vnd.dlite-tiff",
                "image/vnd.dlite-eps",
            ]
        ],
        Field(description=ResourceConfig.model_fields["mediaType"].description),
    ] = None

    # Parser config
    image_label: Annotated[
        str,
        Field(
            description="Label to assign to the image in the collection.",
        ),
    ] = "image"


class DLiteImageParserConfig(ParserConfig):
    """Parser config for DLite image parser."""

    parserType: Annotated[
        Literal["image/vnd.dlite-image"],
        Field(description=ParserConfig.model_fields["parserType"].description),
    ] = "image/vnd.dlite-image"

    configuration: Annotated[
        DLiteImageConfig,
        Field(
            description="Image parse strategy-specific configuration.",
        ),
    ] = DLiteImageConfig()

    entity: Annotated[
        AnyHttpUrl,  # Keep this type to avoid changing the original type
        Field(description=ParserConfig.model_fields["entity"].description),
    ] = AnyHttpUrl("http://onto-ns.com/meta/1.0/Image")

    @field_validator("entity", mode="after")
    @classmethod
    def _validate_entity(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        """Ensure that the entity is the Image URI."""
        fixed_uri = "http://onto-ns.com/meta/1.0/Image"

        if value != AnyHttpUrl(fixed_uri):
            raise ValueError(f"Entity must be exactly equal to: {fixed_uri}")

        return value


@dataclass
class DLiteImageParseStrategy:
    """Parse strategy for image files.

    **Registers strategies**:

    - `("mediaType", "image/vnd.dlite-gif")`
    - `("mediaType", "image/vnd.dlite-jpeg")`
    - `("mediaType", "image/vnd.dlite-jpg")`
    - `("mediaType", "image/vnd.dlite-jp2")`
    - `("mediaType", "image/vnd.dlite-png")`
    - `("mediaType", "image/vnd.dlite-tiff")`

    """

    parse_config: DLiteImageParserConfig

    def initialize(self) -> DLiteResult:
        """Initialize."""
        return DLiteResult(
            collection_id=get_collection(
                self.parse_config.configuration.collection_id
            ).uuid
        )

    def get(self) -> DLiteResult:
        """Execute the strategy.

        This method will be called through the strategy-specific
        endpoint of the OTE-API Services.  It assumes that the image to
        parse is stored in a data cache, and can be retrieved via a key
        that is supplied in the parser configuration.

        Returns:
            Reference to a DLite collection ID.

        """
        config = self.parse_config.configuration

        if config.downloadUrl is None:
            raise ValueError("downloadUrl is required.")
        if config.mediaType is None:
            raise ValueError("mediaType is required.")

        # Configuration for ImageDataParseStrategy in oteapi-core
        core_config = {
            "parserType": "parser/image",
            "configuration": config.model_dump(),
            "entity": self.parse_config.entity,
        }
        core_config["configuration"]["mediaType"] = (
            "image/" + config.mediaType.split("-")[-1]
        )

        output = create_strategy("parse", core_config).get()

        cache = DataCache()
        data = cache.get(output["image_key"])
        if isinstance(data, bytes):
            data = np.asarray(
                Image.frombytes(
                    data=data,
                    mode=output["image_mode"],
                    size=output["image_size"],
                )
            )
        if not isinstance(data, np.ndarray):
            raise TypeError(
                "Expected image data to be a numpy array, instead it was "
                f"{type(data)}."
            )

        meta = get_meta(str(self.parse_config.entity))
        inst = meta(dimensions=data.shape)
        inst["data"] = data

        coll = get_collection(config.collection_id)
        coll.add(config.image_label, inst)

        update_collection(coll)
        return DLiteResult(collection_id=coll.uuid)
