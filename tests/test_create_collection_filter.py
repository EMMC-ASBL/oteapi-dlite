"""Tests collection filter strategy."""


def test_create_collection_filter():
    """Test the configuration filter."""
    import dlite
    from oteapi.models.filterconfig import FilterConfig

    from oteapi_dlite.strategies.create_collection_filter import (
        CreateCollectionFilterStrategy,
    )

    config = FilterConfig(filterType="create_collection")

    session = {}

    collfilter = CreateCollectionFilterStrategy(config)
    session.update(collfilter.initialize(session))

    assert "collection_id" in session
    coll_id = session["collection_id"]
    coll = dlite.get_collection(coll_id)
    assert isinstance(coll, dlite.Collection)
