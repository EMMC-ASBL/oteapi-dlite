"""Strategy class for parsing an image to a DLite instance."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from io import BytesIO
from random import getrandbits
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import numpy as np
from dlite.datamodel import DataModel
from oteapi.datacache.datacache import DataCache
from oteapi.models import SessionUpdate
from oteapi.strategies.parse.image import ImageDataParseStrategy
from PIL import Image
from pydantic import BaseModel, Field, HttpUrl

if TYPE_CHECKING:  # pragma: no cover
    from dlite import Instance
    from oteapi.models.resourceconfig import ResourceConfig


class DLiteImageConfig(BaseModel):
    """Configuration for DLite image parser."""

    def __init__(self, **kwargs) -> None:
        """Initialize image configuration object."""
        super().__init__()
        if not kwargs:
            return
        config = kwargs.copy()
        if "crop" in config:
            self.crop = config.pop("crop", self.crop)
        if "given_id" in config:
            self.given_id = config.pop("given_id", self.given_id)
        if "metadata" in config:
            self.metadata = config.pop("metadata", self.metadata)
        if config:
            self.configuration = config

    configuration: Optional[Dict[str, Any]] = Field(
        None, description="Specific image configuration parameters."
    )

    crop: Optional[Tuple] = Field(
        None, description="Cropping rectangle. The whole image if None."
    )

    given_id: Optional[str] = Field(None, description="Optional id for new instance.")

    metadata: Optional[HttpUrl] = Field(
        None,
        description=(
            "URI of DLite metadata to return.  If not provided, the metadata "
            "will be inferred from the image file."
        ),
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

    META_PREFIX = "http://onto-ns.com/meta/1.0/generated_from_"
    parse_config: "ResourceConfig"

    def initialize(self, session: "Optional[Dict[str, Any]]" = None) -> "SessionUpdate":
        """Initialize."""
        SessionUpdate()

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> "SessionUpdate":
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
        if session and "key" in session:
            key = session["key"]
        elif "key" in self.parse_config.configuration:
            key = self.parse_config.configuration["key"]
        else:
            raise RuntimeError("Image parser needs an image to parse")

        image_config = DLiteImageConfig(**self.parse_config.configuration)
        if image_config.metadata:
            raise NotImplementedError(
                "User-defined metadata for images not implemented"
            )

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
        meta = self.create_meta(
            image,
            self.parse_config.mediaType,
            data.dtype.name,
        )
        inst = meta(
            dims=[image.height, image.width, len(image.getbands())],
            id=image_config.given_id,
        )
        inst["data"] = data
        if image.format:
            inst["format"] = image.format
        # if image.info:
        #     inst["info"] = str(image.info)
        # if "frames" in inst:
        #     inst["frames"] = getattr(image, "n_frames")
        #     inst["animated"] = getattr(image, "is_animated", False)

        inst.incref()
        return SessionUpdate(uuid=inst.uuid)

    @classmethod
    def create_meta(cls, image: Image, media_type: str, data_type: str) -> "Instance":
        """Create DLite metadata from Image `image`."""

        image_format = media_type.rpartition("/")[2]
        rnd = getrandbits(128)
        uri = f"{cls.META_PREFIX}{image_format}_{rnd:0x}"
        metadata = DataModel(
            uri, description=f"Generated datamodel from {image_format} file."
        )
        metadata.add_dimension("nheight", "Vertical number of pixels.")
        metadata.add_dimension("nwidth", "Horizontal number of pixels.")
        metadata.add_dimension("nbands", "Number of bands per pixel.")
        metadata.add_property(
            "data",
            data_type,
            ["nheight", "nwidth", "nbands"],
            description="The image contents.",
        )
        if getattr(image, "format", None):
            metadata.add_property(
                "format",
                "string",
                description="The image format.",
            )
        # if getattr(image, "info", None):
        #     metadata.add_property(
        #         "info",
        #         "string",
        #         description="Additional information.",
        #     )
        # if getattr(image, "n_frames", 1) > 1:
        #     metadata.add_property(
        #         "frames",
        #         dlite.UIntType,
        #         description="Number of frames in the file.",
        #     )
        #     metadata.add_property(
        #         "animated",
        #         dlite.BoolType,
        #         description="If the file contains an animation.",
        #     )
        return metadata.get()
