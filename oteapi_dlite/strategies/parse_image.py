"""Strategy class for parsing xlsx to a DLite instance."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from pathlib import Path
from random import getrandbits

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field, HttpUrl
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import dlite

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict, Optional, Tuple

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
        if "id" in config:
            self.id = config.pop("id", self.id)
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

    id: Optional[str] = Field(None, description="Optional id for new instance.")

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

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "Dict[str, Any]":
        """Initialize."""
        return {}

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> "Dict[str, Any]":
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            DLite instance.

        """
        from oteapi.datacache.datacache import DataCache
        from oteapi.strategies.parse.image import ImageDataParseStrategy

        image_config = DLiteImageConfig(**self.parse_config.configuration)
        if image_config.metadata:
            raise NotImplementedError(
                "User-defined metadata for images not implemented"
            )
        if "key" not in session:
            raise RuntimeError("Image parser needs an image to parse")
        key = session["key"]
        dc = DataCache()

        if image_config.crop:
            # Crop the image before creating a DLite datamodel from it
            # NOTE: Change this when ImageDataParseStrategy.get()
            # uses datacache key as input
            suffix = "." + self.parse_config.mediaType.rpartition("/")[2]
            with dc.getfile(key, suffix=suffix) as tmp_file:
                tmp_config = self.parse_config.copy()
                tmp_config.configuration["filename"] = tmp_file.name
                tmp_config.configuration["localpath"] = tmp_file.parent
                parsed = ImageDataParseStrategy(tmp_config).get().parsedOutput
            cropped_file = Path(parsed["cropped_filename"])
            key = dc.add(cropped_file.read_bytes())
            cropped_file.unlink()

        with dc.getfile(key) as source:
            temp = Image.open(source)
            image = temp.copy()
            temp.close()

        data = np.asarray(image)
        if np.ndim(data) == 2:
            data.shape = (data.shape[0], data.shape[1], 1)
        meta = __class__.create_meta(
            image,
            self.parse_config.mediaType,
            data.dtype.name,
        )
        inst = meta(
            dims=[image.height, image.width, len(image.getbands())],
            id=image_config.id,
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
        return {"uuid": inst.uuid}

    @classmethod
    def create_meta(
        cls, image: Image, media_type: str, data_type: str
    ) -> "dlite.Instance":
        """Create DLite metadata from Image `image`."""
        from dlite.datamodel import DataModel

        format = media_type.rpartition("/")[2]
        rnd = getrandbits(128)
        uri = f"{__class__.META_PREFIX}{format}_{rnd:0x}"
        metadata = DataModel(
            uri, description=f"Generated datamodel from {format} file."
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
