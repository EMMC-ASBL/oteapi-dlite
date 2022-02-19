"""Tests collection filter strategy."""


def test_filter_collection():
    """Test the configuration filter."""
    import dlite
    from oteapi.models.filterconfig import FilterConfig

    from oteapi_dlite.strategies.filter_collection import DLiteCollectionFilterstrategy

    config = FilterConfig()

    session = {}

    collfilter = DLiteCollectionFilterstrategy(config)
    session.update(collfilter.initialize(session))

    assert "collection_id" in session
    coll = session["collection_id"]
    assert isinstance(coll, dlite.Collection)
