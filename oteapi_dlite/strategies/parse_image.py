"""Strategy class for parsing an image to a DLite instance."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Optional, Tuple

import dlite
import numpy as np
from oteapi.datacache.datacache import DataCache
from oteapi.strategies.parse.image import ImageDataParseStrategy
from PIL import Image
from pydantic import BaseModel, Field

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_meta

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict

    from dlite import Instance
    from oteapi.models.resourceconfig import ResourceConfig


class DLiteImageConfig(BaseModel):
    """Configuration for DLite image parser."""

    crop: Optional[Tuple] = Field(
        None, description="Cropping rectangle. The whole image if None."
    )
    image_label: str = Field(
        "image",
        description="Label to assign to the image in the collection.",
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

    parse_config: "ResourceConfig"

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

        if "key" in session:
            key = session["key"]
        elif "key" in self.parse_config.configuration:
            key = self.parse_config.configuration["key"]
        else:
            raise RuntimeError("Image parser needs an image to parse")

        image_config = DLiteImageConfig(**self.parse_config.configuration)

        with DataCache().getfile(
            key, suffix=self.parse_config.mediaType.split("/")[1]
        ) as tmp_file:
            if image_config.crop:
                tmp_config = self.parse_config.copy()
                tmp_config.configuration["filename"] = tmp_file.name
                tmp_config.configuration["localpath"] = tmp_file.parent
                image = Image.open(
                    BytesIO(ImageDataParseStrategy(tmp_config).get().content)
                )
            else:
                image = Image.open(tmp_file).copy()

        data = np.asarray(image)
        if np.ndim(data) == 2:
            data.shape = (data.shape[0], data.shape[1], 1)
        meta = get_meta("http://onto-ns.com/meta/1.0/Image")
        inst = meta(dims=[image.height, image.width, len(image.getbands())])
        inst["data"] = data

        coll = dlite.get_collection(session["collection_id"])
        coll.add(image_config.image_label, inst)

        return DLiteSessionUpdate(collection_id=coll.uuid)
