"""Tests generate strategy."""

# if True:
from __future__ import annotations


def test_generate():
    """Test generate strategy."""
    from pathlib import Path

    import dlite
    from oteapi.datacache import DataCache

    from oteapi_dlite.strategies.generate import (
        DLiteGenerateConfig,
        DLiteGenerateStrategy,
    )
    from oteapi_dlite.utils import get_meta

    thisdir = Path(__file__).resolve().parent
    outdir = thisdir / ".." / "output"

    config = DLiteGenerateConfig(
        functionType="application/vnd.dlite-generate",
        configuration={
            "label": "image",
            "driver": "json",
            "location": str(outdir / "image.json"),
            "options": "mode=w",
        },
    )

    coll = dlite.Collection()

    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]], [[3], [4]]]
    coll.add("image", image)

    session = {"collection_id": coll.uuid}
    DataCache().add(coll.asjson(), key=coll.uuid)

    generator = DLiteGenerateStrategy(config)
    session.update(generator.initialize(session))

    generator = DLiteGenerateStrategy(config)
    session.update(generator.get(session))

    # Check that the data in the newly created generated json file matches our
    # image instance.
    # Fefore loading the generated file, we delete the original image instance
    # to ensure that we are not just fetching it from the dlite cache...
    image_dict = image.asdict()
    del image
    image2 = dlite.Instance.from_location(
        "json", outdir / "image.json", "mode=r"
    )
    assert image2.asdict() == image_dict
