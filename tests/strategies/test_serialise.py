"""Tests serialise strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from oteapi.interfaces import IFilterStrategy


def test_serialise(tmp_path: Path) -> None:
    """Test the serialise filter."""
    import dlite
    from oteapi.datacache import DataCache
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.serialise import (
        SerialiseFilterConfig,
        SerialiseStrategy,
    )
    from oteapi_dlite.utils import get_meta

    coll = dlite.Collection()

    config = SerialiseFilterConfig(
        filterType="dlite_serialise",
        configuration={
            "driver": "json",
            "location": str(tmp_path / "coll.json"),
            "options": "mode=w",
            # "labels": ["image"],
            "collection_id": coll.uuid,
        },
    )

    DataCache().add(coll.asjson(), key=coll.uuid)

    session = SerialiseStrategy(config).initialize()

    # Imitate other filters adding stuff to the collection
    coll.add_relation("subject", "predicate", "object")
    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]], [[3], [4]]]
    coll.add("image", image)

    populate_config_from_session(session, config)

    SerialiseStrategy(config).get()

    assert (tmp_path / "coll.json").exists()
