"""Trivial filter that adds an empty collection to the session."""
# pylint: disable=unused-argument
from typing import TYPE_CHECKING, Any, Dict

import dlite
from oteapi.datacache import DataCache
from oteapi.models import FilterConfig
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate

if TYPE_CHECKING:
    from typing import Optional


@dataclass
class CreateCollectionStrategy:
    """Trivial filter that adds an empty collection to the session.

    **Registers strategies**:

    - `("filterType", "dlite/create-collection")`

    """

    filter_config: FilterConfig

    # Find a better way to keep collections alive!!!
    # Need to be `Any`, because otherwise `pydantic` complains.
    collection_refs: Dict[str, Any] = Field(
        {},
        description="A dictionary of DLite Collections.",
    )

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Initialize."""
        if session is None:
            raise ValueError("Missing session")
        if "collection_id" in session:
            raise KeyError("`collection_id` already exists in session.")

        coll = dlite.Collection()

        # Make sure that collection stays alive
        # It will never be deallocated...
        coll._incref()  # pylint: disable=protected-access

        # Store the collection in the data cache
        cache = DataCache()
        cache.add(value=coll.asjson(), key=coll.uuid)

        return DLiteSessionUpdate(collection_id=coll.uuid)

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Execute the strategy."""
        if session is None:
            raise ValueError("Missing session")
        return DLiteSessionUpdate(collection_id=session["collection_id"])
