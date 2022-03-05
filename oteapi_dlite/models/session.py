"""Pydantic data models for DLite."""
from typing import Optional

# import dlite
from oteapi.models import SessionUpdate
from pydantic import Field

# def new_collection():
#    """Returns an UUID of a new collection."""
#    coll = dlite.Collection()
#
#    # Make sure that the collection does not go out of scope
#    # Note, this will lead memory unless the user explicit calls
#    # decref() on it:
#    #
#    #     coll = dlite.get_collection(UUID)
#    #     coll.decref()
#    #
#    coll.incref()
#
#    return coll.uuid


class DLiteSessionUpdate(SessionUpdate):
    """Class for returning values from DLite strategies."""

    collection_id: Optional[str] = Field(
        {},  # default_factory=new_collection,
        description="A reference to a DLite collection.",
    )
