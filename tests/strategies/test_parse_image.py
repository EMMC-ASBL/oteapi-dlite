"""Test the image formats in the image parse strategy."""
# pylint: disable=too-many-locals
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional, Tuple


def test_image_config() -> None:
    """Test the DLiteImageConfig class."""
    from oteapi.models.resourceconfig import ResourceConfig

    from oteapi_dlite.strategies.parse_image import DLiteImageConfig

    config = ResourceConfig(
        downloadUrl="file://dummy",
        mediaType="image/png",
        configuration={
            "crop": (0, 0, 100, 100),
            "image_label": "test_image",
        },
    )
    image_config = DLiteImageConfig(**config.configuration)
    assert image_config.crop == config.configuration["crop"]
    assert image_config.image_label == config.configuration["image_label"]


@pytest.mark.parametrize("crop_rect", [None, (100, 100, 250, 200)])
@pytest.mark.parametrize(
    "test_file, target_file",
    (
        # ("sample_1280_853.gif", "sample_150_100.gif"),
        # ("sample_1280_853.jpeg", "sample_150_100.jpeg"),
        # ("sample_1280_853.jpg", "sample_150_100.jpeg"),
        # ("sample1.jp2", "sample1_150_100.jp2"), DISABLED BECAUSE SLOW
        ("sample_640_426.png", None),
        # ("sample_640_426.tiff", None),
    ),
)
def test_image(
    test_file: str,
    target_file: "Optional[str]",
    crop_rect: "Optional[Tuple[int, int, int, int]]",
    static_files: "Path",
) -> None:
    """Test parsing an image format."""
    import dlite
    import numpy as np
    from oteapi.datacache import DataCache
    from oteapi.models import AttrDict, ResourceConfig
    from PIL import Image

    from oteapi_dlite.strategies.parse_image import DLiteImageParseStrategy

    sample_file = static_files / test_file

    orig_key = DataCache().add(sample_file.read_bytes())
    config = ResourceConfig(
        downloadUrl="file://dummy.host/" + str(sample_file),
        mediaType="image/" + test_file.rpartition(".")[2],
        configuration={
            "image_label": "test_image",
            "crop": crop_rect,
        },
    )
    coll = dlite.Collection()
    session = AttrDict(
        collection_id=coll.uuid,
        key=orig_key,
    )
    parser = DLiteImageParseStrategy(config)
    output = parser.get(session)
    assert "collection_id" in output

    coll = dlite.get_collection(session.collection_id)
    inst = coll.get("test_image")
    inst.meta.save("json", "Image.json", "mode=w")

    # Compare data instance contents to expected values
    assert inst.meta.uri.startswith("http://onto-ns.com/meta")
    dims = inst.dimensions
    if crop_rect:
        assert dims["nheight"] == crop_rect[3] - crop_rect[1]
        assert dims["nwidth"] == crop_rect[2] - crop_rect[0]
        if target_file:
            # Pixel values in instance will not match those in the
            # cropped subset of the original image, so we must compare
            # with a pre-defined target
            target = Image.open(static_files / target_file)
        else:
            target = Image.open(sample_file)
    else:
        target = Image.open(sample_file)

    assert dims["nbands"] == len(target.getbands())
    if "format" in inst.properties:
        assert inst.format == target.format

    subset = np.asarray(target)
    if np.ndim(subset) == 2:
        subset.shape = (subset.shape[0], subset.shape[1], 1)
    if crop_rect and not target_file:
        subset = subset[
            crop_rect[1] : crop_rect[3],
            crop_rect[0] : crop_rect[2],
            :,
        ]

    # Compare pixel values
    assert np.all(np.equal(inst.data, subset))
