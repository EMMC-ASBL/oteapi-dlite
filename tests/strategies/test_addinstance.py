"""Tests add instance strategy."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from oteapi.interfaces import IFilterStrategy


def test_create_collection() -> None:
    """Test the create_collection filter."""
    import dlite

    from oteapi_dlite.strategies.function import DLiteAddInstanceStrategy
 
    # Need to add storage
    # Need to 
    config = {"datamodel": "some uuid",
            "value": a dict,
            "label": "name"}
    

    session = {}

    collfunction: "IFunctionStrategy" = DLiteAddInstanceStrategy(config)
    session.update(collfunction.initialize(session))

    assert "collection_id" in session
    coll_id = session["collection_id"]
    coll = dlite.get_collection(coll_id)
    assert isinstance(coll, dlite.Collection)

    collfunction = DLiteAddInstanceStrategy(config)
    session.update(collfunction.get(session))
    assert "collection_id" in session
    assert session["collection_id"] == coll_id
