"""Filter that removes all but specified instances in the collection."""
# pylint: disable=unused-argument
from typing import TYPE_CHECKING

from oteapi.models import FilterConfig

# from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:
    from typing import Any, Dict, Optional


# class DLiteFilterConfig(AttrDict):
#    """Configuration for a DLite filter filter."""
#    labels: List[str] = Field(
#        ...,
#        description='List of labels to keep in collection.',
#    )
#
#
# class DLiteFilterConfig(FilterConfig):
#    """DLite generate strategy config."""
#
#    configuration: DLiteFilterConfig = Field(
#        ..., description="DLite filter strategy-specific configuration."
#    )


@dataclass
class DLiteFilterStrategy:
    """Filter that removes all but specified instances in the collection.

    The `query` configuration should be a comma-separated list of labels
    to keep in the collection.  All other labels will be removed.

    **Registers strategies**:

    - `("filterType", "dlite/filter")`

    WARNING: This is a first simple implementation. The behaviour of this
    strategy may change.
    """

    filter_config: FilterConfig

    def initialize(
        self,
        session: "Optional[Dict[str, Any]]" = None,
    ) -> DLiteSessionUpdate:
        """Initialize."""
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Execute the strategy."""
        config = self.filter_config
        labels_to_keep = config.query.split(",")

        to_remove = []
        coll = get_collection(session)
        for label in coll.get_labels():
            if label not in labels_to_keep:
                to_remove.append(label)

        for label in to_remove:
            coll.remove(label)

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)
