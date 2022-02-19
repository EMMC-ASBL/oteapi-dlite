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
class DLiteCollectionFilterStrategy:
    """Trivial filter that adds an empty collection to the session.

    **Registers strategies**:

    - `("filterType", "filter/collection")`

    """

    filter_config: "FilterConfig"

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "Dict[str, Any]":
        """Initialize."""
        if session is None:
            raise ValueError("Missing session")
        if "collection_id" in session:
            raise KeyError("`collection_id` already exists in session.")
        return SessionUpdate(collection_id=dlite.Collection())

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> "Dict[str, Any]":
        """Execute the strategy."""
        return SessionUpdate()
