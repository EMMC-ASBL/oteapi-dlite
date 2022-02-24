"""Test the image formats in the image parse strategy."""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image


def test_image_config():
    """Test the DLiteImageConfig class."""
    from oteapi.models.resourceconfig import ResourceConfig

    from oteapi_dlite.strategies.parse_image import DLiteImageConfig

    config = ResourceConfig(
        downloadUrl="file://dummy",
        mediaType="image/png",
        configuration={
            "crop": (0, 0, 100, 100),
            "given_id": "abcdef",
            "new_key_just_for_testing": 3.14,
        },
    )
    image_config = DLiteImageConfig(**config.configuration)
    assert image_config.crop == config.configuration["crop"]
    assert image_config.given_id == config.configuration["given_id"]
    assert not image_config.metadata
    assert "new_key_just_for_testing" in image_config.configuration


@pytest.mark.parametrize("crop_rect", [None, (100, 100, 250, 200)])
@pytest.mark.parametrize(
    "test_file, target_file",
    (
        ("sample_1280_853.gif", "sample_150_100.gif"),
        ("sample_1280_853.jpeg", "sample_150_100.jpeg"),
        ("sample_1280_853.jpg", "sample_150_100.jpeg"),
        # ("sample1.jp2", "sample1_150_100.jp2"), DISABLED BECAUSE SLOW
        ("sample_640_426.png", None),
        ("sample_640_426.tiff", None),
    ),
)
def test_image(test_file, target_file, crop_rect) -> None:
    """Test parsing an image format."""
    import dlite
    from oteapi.datacache.datacache import DataCache
    from oteapi.models.resourceconfig import ResourceConfig

    from oteapi_dlite.strategies.parse_image import DLiteImageParseStrategy

    this_dir = Path(__file__).resolve().parent
    orig_key = DataCache().add((this_dir / test_file).read_bytes())
    config = ResourceConfig(
        downloadUrl="file://dummy.host/" + str(this_dir / test_file),
        mediaType="image/" + test_file.rpartition(".")[2],
        configuration={"crop": crop_rect},
    )
    inst = DLiteImageParseStrategy(config).get(session={"key": orig_key})

    # Compare data instance contents to expected values
    contents = dlite.get_instance(inst["uuid"]).asdict()
    assert contents["meta"].startswith(
        DLiteImageParseStrategy.META_PREFIX,
    )
    dims = contents["dimensions"]
    if crop_rect:
        assert dims["nheight"] == crop_rect[3] - crop_rect[1]
        assert dims["nwidth"] == crop_rect[2] - crop_rect[0]
        if target_file:
            # Pixel values in instance will not match those in the
            # cropped subset of the original image, so we must compare
            # with a pre-defined target
            target = Image.open(this_dir / target_file)
        else:
            target = Image.open(this_dir / test_file)
    else:
        target = Image.open(this_dir / test_file)

    assert dims["nbands"] == len(target.getbands())
    if "format" in contents["properties"]:
        assert contents["properties"]["format"] == target.format

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
    assert np.all(np.equal(contents["properties"]["data"], subset))
