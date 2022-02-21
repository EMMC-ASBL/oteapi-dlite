"""Test the image formats in the image parse strategy."""
from pathlib import Path

import numpy as np
from PIL import Image
import pytest


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

    media_type = "image/" + test_file.rpartition(".")[2]
    dc = DataCache()
    this_dir = Path(__file__).resolve().parent
    orig_key = dc.add((this_dir / test_file).read_bytes())
    config = ResourceConfig(
        downloadUrl="file://dummy",
        mediaType=media_type,
        configuration={"crop": crop_rect},
    )
    parser = DLiteImageParseStrategy(config)
    inst = parser.get(session={"key": orig_key})

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
