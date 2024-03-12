"""Test to store the entire collection with the generate strategy."""

from pathlib import Path

import dlite

from oteapi_dlite.strategies.generate import (
    DLiteGenerateConfig,
    DLiteGenerateStrategy,
)
from oteapi_dlite.utils import get_meta

thisdir = Path(__file__).resolve().parent
entitydir = thisdir / ".." / "entities"
outdir = thisdir / ".." / "output"

coll = dlite.Collection()
config = DLiteGenerateConfig(
    functionType="application/vnd.dlite-generate",
    configuration={
        "driver": "json",
        "location": str(outdir / "coll.json"),
        "options": "mode=w",
        "store_collection": True,
        "collection_id": coll.uuid,
    },
)

Image = get_meta("http://onto-ns.com/meta/1.0/Image")
image = Image([2, 2, 1])
image.data = [[[1], [2]], [[3], [4]]]
coll.add("image", image)
coll.add_relation("image", "rdf:type", "onto:Image")
coll.add_relation("image", "dcterms:title", "Madonna")

generator = DLiteGenerateStrategy(config)
generator.initialize()

generator = DLiteGenerateStrategy(config)
generator.get()


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
assert coll.nrelations == 5
assert coll["image"] == image
