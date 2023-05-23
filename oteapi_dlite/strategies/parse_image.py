"""Strategy class for parsing an image to a DLite instance."""
import logging
from typing import TYPE_CHECKING

from oteapi.datacache import DataCache
from oteapi.models import ResourceConfig
from oteapi.strategies.parse.image import (
    ImageDataParseStrategy,
    ImageParserConfig,
    ImageParserResourceConfig,
)
from pydantic import Extra, Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, get_meta, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict, Optional


LOGGER = logging.getLogger("oteapi_dlite.strategies")
LOGGER.setLevel(logging.DEBUG)


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

    - `("mediaType", "image/vnd.dlite-gif")`
    - `("mediaType", "image/vnd.dlite-jpeg")`
    - `("mediaType", "image/vnd.dlite-jpg")`
    - `("mediaType", "image/vnd.dlite-jp2")`
    - `("mediaType", "image/vnd.dlite-png")`
    - `("mediaType", "image/vnd.dlite-tiff")`

    """

    parse_config: DLiteImageResourceConfig

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Initialize."""
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
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
        conf = self.parse_config.dict()
        conf["configuration"] = ImageParserConfig(
            **config.dict(),
            extra=Extra.ignore,
        )
        conf["mediaType"] = "image/" + conf["mediaType"].split("-")[-1]
        core_config = ImageParserResourceConfig(**conf)

        parse_strategy_session = ImageDataParseStrategy(core_config).initialize(
            session
        )
        output = ImageDataParseStrategy(core_config).get(parse_strategy_session)

        cache = DataCache()
        data = cache.get(output["image_key"])

        meta = get_meta("http://onto-ns.com/meta/1.0/Image")
        inst = meta(dimensions=data.shape)
        inst["data"] = data

        LOGGER.info("session: %s", session)

        coll = get_collection(session)
        coll.add(config.image_label, inst)

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)
