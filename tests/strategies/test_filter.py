"""Tests filter strategies."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from oteapi.interfaces import IFilterStrategy


def test_create_collection() -> None:
    """Test the create_collection filter."""
    import dlite

    from oteapi_dlite.strategies.filter import CreateCollectionStrategy

    config = {"filterType": "dlite/create_collection"}

    session = {}

    collfilter: "IFilterStrategy" = CreateCollectionStrategy(config)
    session.update(collfilter.initialize(session))

    assert "collection_id" in session
    coll_id = session["collection_id"]
    coll = dlite.get_collection(coll_id)
    assert isinstance(coll, dlite.Collection)

    collfilter = CreateCollectionStrategy(config)
    session.update(collfilter.get(session))
    assert "collection_id" in session
    assert session["collection_id"] == coll_id
