"""Test to store the entire collection with the generate strategy."""

from __future__ import annotations

from pathlib import Path

import dlite
from oteapi.datacache import DataCache

from oteapi_dlite.strategies.generate import (
    DLiteGenerateConfig,
    DLiteGenerateStrategy,
)
from oteapi_dlite.utils import get_meta

thisdir = Path(__file__).resolve().parent
entitydir = thisdir / ".." / "entities"
outdir = thisdir / ".." / "output"


config = DLiteGenerateConfig(
    functionType="application/vnd.dlite-generate",
    configuration={
        "driver": "json",
        "location": str(outdir / "coll.json"),
        "options": "mode=w",
        "store_collection": True,
    },
)

coll = dlite.Collection("coll_id")

Image = get_meta("http://onto-ns.com/meta/1.0/Image")
image = Image([2, 2, 1])
image.data = [[[1], [2]], [[3], [4]]]
coll.add("image", image)
coll.add_relation("image", "rdf:type", "onto:Image")
coll.add_relation("image", "dcterms:title", "Madonna")


session = {"collection_id": coll.uuid}
DataCache().add(coll.asjson(), key=coll.uuid)

generator = DLiteGenerateStrategy(config)
session.update(generator.initialize(session))

generator = DLiteGenerateStrategy(config)
session.update(generator.get(session))


# Check that the data in the newly created generated json file matches our
# collection.
# Before loading the generated file, we delete the original collection
# to ensure that we are not just fetching it from the dlite cache...
del coll
with dlite.Storage("json", outdir / "coll.json", "mode=r") as s:
    # Assume we don't know the collection uuid, but we know that there is only
    # one collection in the json file
    (coll_uuid,) = s.get_uuids("http://onto-ns.com/meta/0.1/Collection")
    coll = s.load(id=coll_uuid)
assert coll.uri == "coll_id"
assert coll.nrelations == 5
assert coll["image"] == image
