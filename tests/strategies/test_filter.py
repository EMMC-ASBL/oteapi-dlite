"""Tests filter strategies."""
from pathlib import Path

import dlite

from oteapi_dlite.strategies.filter import (
    DLiteFilterConfig,
    DLiteFilterStrategy,
)
from oteapi_dlite.utils import get_meta

thisdir = Path(__file__).resolve().parent
entitydir = thisdir / ".." / "entities"
outdir = thisdir / ".." / "output"

Image = get_meta("http://onto-ns.com/meta/1.0/Image")
image1 = Image([2, 2, 1])
image2 = Image([2, 2, 1])
image3 = Image([2, 2, 1])
image4 = Image([2, 2, 1])
innercoll = dlite.Collection()
innercoll.add("im1", image1)
innercoll.add("im2", image2)

coll = dlite.Collection()
coll.add("innercoll", innercoll)
coll.add("image1", image1)
coll.add("image2", image2)
coll.add("image3", image3)
coll.add("image4", image4)


# Test simple use of query
config = DLiteFilterConfig(
    filterType="dlite/filter",
    query="^im",
    configuration={},
)
coll0 = coll.copy()
session = {"collection_id": coll0.uuid}

strategy = DLiteFilterStrategy(config)
session.update(strategy.initialize(session))

strategy = DLiteFilterStrategy(config)
session.update(strategy.get(session))

assert set(coll0.get_labels()) == set(
    [
        "image1",
        "image2",
        "image3",
        "image4",
    ]
)


# Same test as above, but use use `keep_label` instead of `query`
config = DLiteFilterConfig(
    filterType="dlite/filter",
    configuration={
        "keep_label": "^im",
    },
)
coll1 = coll.copy()
session = {"collection_id": coll1.uuid}

strategy = DLiteFilterStrategy(config)
session.update(strategy.initialize(session))

strategy = DLiteFilterStrategy(config)
session.update(strategy.get(session))

assert set(coll1.get_labels()) == set(
    [
        "image1",
        "image2",
        "image3",
        "image4",
    ]
)


# Test combining remove and keep
config = DLiteFilterConfig(
    filterType="dlite/filter",
    configuration={
        "remove_datamodel": Image.uri,
        "keep_label": "(image2)|(image4)",
        "keep_referred": False,
    },
)
coll2 = coll.copy()
session = {"collection_id": coll2.uuid}

strategy = DLiteFilterStrategy(config)
session.update(strategy.initialize(session))

strategy = DLiteFilterStrategy(config)
session.update(strategy.get(session))

assert set(coll2.get_labels()) == set(
    [
        "innercoll",
        "image2",
        "image4",
    ]
)


# Test with keep_referred=True
config = DLiteFilterConfig(
    filterType="dlite/filter",
    configuration={
        "remove_datamodel": Image.uri,
        "keep_label": "(image2)|(image4)",
        "keep_referred": True,
    },
)
coll3 = coll.copy()
session = {"collection_id": coll3.uuid}

strategy = DLiteFilterStrategy(config)
session.update(strategy.initialize(session))

strategy = DLiteFilterStrategy(config)
session.update(strategy.get(session))

assert set(coll3.get_labels()) == set(
    [
        "innercoll",
        "image1",
        "image2",
        "image4",
    ]
)
