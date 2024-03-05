"""Strategy class for parsing an image to a DLite instance."""

import logging
from typing import TYPE_CHECKING, Annotated

import numpy as np
from oteapi.datacache import DataCache
from oteapi.models import ResourceConfig
from oteapi.strategies.parse.image import (
    ImageConfig,
    ImageDataParseStrategy,
    ImageParserConfig,
)
from PIL import Image
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, get_meta, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Optional


LOGGER = logging.getLogger("oteapi_dlite.strategies")
LOGGER.setLevel(logging.DEBUG)


class DLiteImageConfig(ImageParserConfig):
    """Configuration for DLite image parser."""

    image_label: Annotated[
        str,
        Field(
            description="Label to assign to the image in the collection.",
        ),
    ] = "image"
    collection_id: Annotated[
        Optional[str], Field(description="A reference to a DLite collection.")
    ] = None


class DLiteImageResourceConfig(ResourceConfig):
    """Resource config for DLite image parser."""

    configuration: Annotated[
        DLiteImageConfig,
        Field(
            description="Image parse strategy-specific configuration.",
        ),
    ] = DLiteImageConfig()


@dataclass
class DLiteImageParseStrategy:
    """Parse strategy for image files.

    **Registers strategies**:

    - `("parserType", "image/vnd.dlite-gif")`
    - `("parserType", "image/vnd.dlite-jpeg")`
    - `("parserType", "image/vnd.dlite-jpg")`
    - `("parserType", "image/vnd.dlite-jp2")`
    - `("parserType", "image/vnd.dlite-png")`
    - `("parserType", "image/vnd.dlite-tiff")`

    """

    parse_config: DLiteImageResourceConfig

    def initialize(self) -> DLiteSessionUpdate:
        """Initialize."""
        if self.parse_config.configuration.collection_id:
            return DLiteSessionUpdate(
                collection_id=self.parse_config.configuration.collection_id
            )
        return DLiteSessionUpdate(collection_id=get_collection().uuid)

    def get(self) -> DLiteSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific
        endpoint of the OTE-API Services.  It assumes that the image to
        parse is stored in a data cache, and can be retrieved via a key
        that is supplied in either the session (highest priority)
        or in the parser configuration (lowest priority).

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            DLite instance.
        """
        config = self.parse_config.configuration

        # Configuration for ImageDataParseStrategy in oteapi-core
        conf = self.parse_config.model_dump()
        conf["configuration"] = ImageParserConfig(
            **config.model_dump(), extra="ignore"
        )
        conf["parserType"] = "image/" + conf["parserType"].split("-")[-1]
        core_config = ImageConfig(**conf)

        ImageDataParseStrategy(core_config).initialize()
        output = ImageDataParseStrategy(core_config).get()

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

        meta = get_meta("http://onto-ns.com/meta/1.0/Image")
        inst = meta(dimensions=data.shape)
        inst["data"] = data

        coll = get_collection(
            collection_id=self.parse_config.configuration.collection_id
        )
        coll.add(config.image_label, inst)

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)
