"""Trivial filter that adds an empty collection to the session."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from typing import TYPE_CHECKING

import dlite
from oteapi.models import SessionUpdate

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from oteapi.models import FilterConfig


@dataclass
class CreateCollectionStrategy:
    """Trivial filter that adds an empty collection to the session.

    **Registers strategies**:

    - `("filterType", "create_collection")`

    """

    filter_config: "FilterConfig"

    def initialize(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Initialize."""
        if session is None:
            raise ValueError("Missing session")
        if "collection_id" in session:
            raise KeyError("`collection_id` already exists in session.")
        coll = dlite.Collection()

        # Save reference to the collection to ensure that it lives as long as
        # the session does
        session["_collection_ref"] = coll

        return SessionUpdate(collection_id=coll.uuid)

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Execute the strategy."""
        return SessionUpdate(collection_id=dlite.Collection())
