"""Test to store the entire collection with the generate strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..conftest import PathsTuple


def test_store_collection(paths: PathsTuple) -> None:
    """Test to store the entire collection with the generate strategy."""
    import dlite
    from oteapi.datacache import DataCache
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.generate import (
        DLiteGenerateConfig,
        DLiteGenerateStrategy,
    )
    from oteapi_dlite.utils import get_meta

    coll = dlite.Collection("coll_id")

    config = DLiteGenerateConfig(
        functionType="application/vnd.dlite-generate",
        configuration={
            "driver": "json",
            "location": str(paths.outputdir / "coll.json"),
            "options": "mode=w",
            "store_collection": True,
            "collection_id": coll.uuid,
        },
    )

    # Create an image instance and add it to the collection
    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]], [[3], [4]]]
    coll.add("image", image)
    coll.add_relation("image", "rdf:type", "onto:Image")
    coll.add_relation("image", "dcterms:title", "Madonna")

    DataCache().add(coll.asjson(), key=coll.uuid)

    session = DLiteGenerateStrategy(config).initialize()

    populate_config_from_session(session, config)

    DLiteGenerateStrategy(config).get()

    # Check that the data in the newly created generated json file matches our
    # collection.
    # Before loading the generated file, we delete the original collection
    # to ensure that we are not just fetching it from the dlite cache...
    del coll
    with dlite.Storage("json", paths.outputdir / "coll.json", "mode=r") as s:
        # Assume we don't know the collection uuid, but we know that there is
        # only one collection in the json file
        (coll_uuid,) = s.get_uuids("http://onto-ns.com/meta/0.1/Collection")
        coll = s.load(id=coll_uuid)
    assert coll.uri == "coll_id"
    assert coll.nrelations == 5
    assert coll["image"] == image
