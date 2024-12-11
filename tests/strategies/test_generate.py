"""Tests generate strategy."""

# if True:
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..conftest import PathsTuple


def test_generate(paths: PathsTuple) -> None:
    """Test generate strategy."""
    import dlite
    from oteapi.datacache import DataCache
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.generate import (
        DLiteGenerateConfig,
        DLiteGenerateStrategy,
    )
    from oteapi_dlite.utils import get_meta

    coll = dlite.Collection()

    config = DLiteGenerateConfig(
        functionType="application/vnd.dlite-generate",
        configuration={
            "label": "image",
            "driver": "json",
            "location": str(paths.outputdir / "image.json"),
            "options": "mode=w",
            "collection_id": coll.uuid,
        },
    )

    # Create an image instance and add it to the collection
    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]], [[3], [4]]]
    coll.add("image", image)

    DataCache().add(coll.asjson(), key=coll.uuid)

    session = DLiteGenerateStrategy(config).initialize()

    populate_config_from_session(session, config)

    DLiteGenerateStrategy(config).get()

    # Check that the data in the newly created generated json file matches our
    # image instance.
    # Fefore loading the generated file, we delete the original image instance
    # to ensure that we are not just fetching it from the dlite cache...
    image_dict = image.asdict()
    del image
    image2 = dlite.Instance.from_location(
        "json", paths.outputdir / "image.json", "mode=r"
    )
    assert image2.asdict() == image_dict
