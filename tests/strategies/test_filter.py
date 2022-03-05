"""Tests filter strategies."""


def test_create_collection():
    """Test the create_collection filter."""
    import dlite
    from oteapi.models.filterconfig import FilterConfig

    from oteapi_dlite.strategies.filter import CreateCollectionStrategy

    config = FilterConfig(filterType="create_collection")

    session = {}

    collfilter = CreateCollectionStrategy(config)
    session.update(collfilter.initialize(session))

    assert "collection_id" in session
    coll_id = session["collection_id"]
    coll = dlite.get_collection(coll_id)
    assert isinstance(coll, dlite.Collection)

    collfilter = CreateCollectionStrategy(config)
    session.update(collfilter.get(session))
    assert "collection_id" in session
    assert session["collection_id"] == coll_id
