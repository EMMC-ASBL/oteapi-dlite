"""Tests relabel strategy."""

from pathlib import Path

import dlite
from oteapi.datacache import DataCache

from oteapi_dlite.strategies.relabel import (
    DLiteRelabelFunctionConfig,
    DLiteRelabelStrategy,
)
from oteapi_dlite.utils import get_meta

thisdir = Path(__file__).resolve().parent
entitydir = thisdir / ".." / "entities"
outdir = thisdir / ".." / "output"


config = DLiteRelabelFunctionConfig(
    functionType="application/vnd.dlite-relabel",
    configuration={
        "datamodel": "http://onto-ns.com/meta/1.0/Image",
        "newlabel": "new-image-label",
    },
)

coll = dlite.Collection()

Image = get_meta("http://onto-ns.com/meta/1.0/Image")
image = Image([2, 2, 1])
image.data = [[[1], [2]], [[3], [4]]]
coll.add("image", image)


session = {"collection_id": coll.uuid}
# DataCache().add(coll.asjson(), key=coll.uuid)

assert set(coll.get_labels()) == {"image"}

relabeler = DLiteRelabelStrategy(config)
session.update(relabeler.initialize(session))

relabeler = DLiteRelabelStrategy(config)
session.update(relabeler.get(session))

assert set(coll.get_labels()) == {"new-image-label"}
