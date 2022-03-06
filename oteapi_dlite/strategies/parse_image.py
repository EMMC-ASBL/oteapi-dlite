"""Strategy class for parsing an image to a DLite instance."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from typing import TYPE_CHECKING

import dlite
from oteapi.datacache import DataCache
from oteapi.models import ResourceConfig
from oteapi.strategies.parse.image import (
    ImageDataParseStrategy,
    ImageParserConfig,
    ImageParserResourceConfig,
)
from pydantic import Extra, Field

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_meta

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict

    from dlite import Instance


class DLiteImageConfig(ImageParserConfig):
    """Configuration for DLite image parser."""

    image_label: str = Field(
        "image",
        description="Label to assign to the image in the collection.",
    )


class DLiteImageResourceConfig(ResourceConfig):
    """Resource config for DLite image parser."""

    configuration: DLiteImageConfig = Field(
        DLiteImageConfig(),
        description="Image parse strategy-specific configuration.",
    )


@dataclass
class DLiteImageParseStrategy:
    """Parse strategy for image files.

    **Registers strategies**:

    - `("mediaType", "image/gif")`
    - `("mediaType", "image/jpeg")`
    - `("mediaType", "image/jpg")`
    - `("mediaType", "image/jp2")`
    - `("mediaType", "image/png")`
    - `("mediaType", "image/tiff")`

    """

    parse_config: DLiteImageResourceConfig

    def initialize(self, session: "Dict[str, Any]" = None) -> DLiteSessionUpdate:
        """Initialize."""
        if session is None:
            raise ValueError("Missing session")
        return DLiteSessionUpdate(collection_id=session["collection_id"])

    def get(self, session: "Dict[str, Any]" = None) -> DLiteSessionUpdate:
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
        if session is None:
            raise ValueError("Missing session")

        config = self.parse_config.configuration

        # Configuration for ImageDataParseStrategy in oteapi-core
        conf = self.parse_config.dict()
        conf["configuration"] = ImageParserConfig(
            **config.dict(),
            extra=Extra.ignore,
        )
        core_config = ImageParserResourceConfig(**conf)

        ImageDataParseStrategy(core_config).initialize(session)
        output = ImageDataParseStrategy(core_config).get(session)

        cache = DataCache()
        data = cache.get(output["image_key"])

        meta = get_meta("http://onto-ns.com/meta/1.0/Image")
        inst = meta(dims=data.shape)
        inst["data"] = data

        coll = dlite.get_collection(session["collection_id"])
        coll.add(config.image_label, inst)

        return DLiteSessionUpdate(collection_id=coll.uuid)
