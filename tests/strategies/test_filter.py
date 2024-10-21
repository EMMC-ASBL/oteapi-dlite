"""Tests filter strategies."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Tuple

    from dlite import Collection, Instance


@pytest.fixture
def initialize_collection() -> "Tuple[Collection, Instance]":
    """Initialize a collection with some images"""
    import dlite

    from oteapi_dlite.utils import get_meta

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

    return coll, Image


def test_simple_use_of_query(
    initialize_collection: "Tuple[Collection, Instance]",
) -> None:
    """Test simple use of query

    Here keeping all instances with label containing "im" in the collection
    """
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.filter import (
        DLiteFilterConfig,
        DLiteFilterStrategy,
    )

    coll, _ = initialize_collection

    config = DLiteFilterConfig(
        filterType="dlite/filter",
        query="^im",
        configuration={"collection_id": coll.uuid},
    )

    session = DLiteFilterStrategy(config).initialize()

    populate_config_from_session(session, config)
    DLiteFilterStrategy(config).get()

    assert set(coll.get_labels()) == set(
        [
            "image1",
            "image2",
            "image3",
            "image4",
        ]
    )


def test_keep_label(
    initialize_collection: "Tuple[Collection, Instance]",
) -> None:
    """Same test as above, but use use `keep_label` instead of `query`"""
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.filter import (
        DLiteFilterConfig,
        DLiteFilterStrategy,
    )

    coll, _ = initialize_collection

    config = DLiteFilterConfig(
        filterType="dlite/filter",
        configuration={
            "keep_label": "^im",
            "collection_id": coll.uuid,
        },
    )

    session = DLiteFilterStrategy(config).initialize()

    populate_config_from_session(session, config)

    DLiteFilterStrategy(config).get()

    assert set(coll.get_labels()) == set(
        [
            "image1",
            "image2",
            "image3",
            "image4",
        ]
    )


def test_combining_remove_and_keep(
    initialize_collection: "Tuple[Collection, Instance]",
) -> None:
    """Test combining remove and keep"""
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.filter import (
        DLiteFilterConfig,
        DLiteFilterStrategy,
    )

    coll, Image = initialize_collection

    config = DLiteFilterConfig(
        filterType="dlite/filter",
        configuration={
            "remove_datamodel": Image.uri,
            "keep_label": "(image2)|(image4)",
            "keep_referred": False,
            "collection_id": coll.uuid,
        },
    )

    session = DLiteFilterStrategy(config).initialize()

    populate_config_from_session(session, config)

    DLiteFilterStrategy(config).get()

    assert set(coll.get_labels()) == set(
        [
            "innercoll",
            "image2",
            "image4",
        ]
    )


def test_keep_referred_true(
    initialize_collection: "Tuple[Collection, Instance]",
) -> None:
    """Test with keep_referred=True"""
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.filter import (
        DLiteFilterConfig,
        DLiteFilterStrategy,
    )

    coll, Image = initialize_collection

    config = DLiteFilterConfig(
        filterType="dlite/filter",
        configuration={
            "remove_datamodel": Image.uri,
            "keep_label": "(image2)|(image4)",
            "keep_referred": True,
            "collection_id": coll.uuid,
        },
    )

    session = DLiteFilterStrategy(config).initialize()

    populate_config_from_session(session, config)

    DLiteFilterStrategy(config).get()

    assert set(coll.get_labels()) == set(
        [
            "innercoll",
            "image1",
            "image2",
            "image4",
        ]
    )
