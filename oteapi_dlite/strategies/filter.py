"""Filter that removes all but specified instances in the collection."""

# pylint: disable=unused-argument
import re
from typing import TYPE_CHECKING, Annotated, Optional

from dlite.utils import get_referred_instances
from oteapi.models import AttrDict, FilterConfig
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class DLiteQueryConfig(AttrDict):
    """Configuration for the DLite filter strategy.

    First the `remove_label` and `remove_datamodel` configurations are
    used to mark matching instances for removal.  If neither
    `remove_label` or `remove_datamodel` are given, all instances are
    marked for removal.

    Then instances matching `keep_label` and `keep_datamodel` are unmarked
    for removal.

    If `keep_referred` is true, any instance that is referred to by
    an instance not marked for removal is also unmarked for removal.

    Finally, the instances that are still marked for removal are removed
    from the collection.
    """

    remove_label: Annotated[
        Optional[str],
        Field(description="Regular expression matching labels to remove."),
    ] = None
    remove_datamodel: Annotated[
        Optional[str],
        Field(
            description="Regular expression matching datamodel URIs to remove.",
        ),
    ] = None
    keep_label: Annotated[
        Optional[str],
        Field(
            description=(
                "Regular expression matching labels to keep. This "
                "configuration overrides `remove_label` and "
                "`remove_datamodel`. Alias for the FilterStrategy `query` "
                "configuration, that is inherited from the oteapi-core Filter "
                "data model."
            ),
        ),
    ] = None
    keep_datamodel: Annotated[
        Optional[str],
        Field(
            description=(
                "Regular expression matching datamodel URIs to keep in "
                "collection. This configuration overrides `remove_label` and "
                "`remove_datamodel`."
            ),
        ),
    ] = None
    keep_referred: Annotated[
        bool,
        Field(
            description=(
                "Whether to keep all instances in the collection that are "
                "directly or indirectly referred to (via ref-types or "
                "collections) by kept instances."
            ),
        ),
    ] = True


class DLiteFilterConfig(FilterConfig):
    """DLite generate strategy config."""

    configuration: Annotated[
        DLiteQueryConfig,
        Field(description="DLite filter strategy-specific configuration."),
    ]


@dataclass
class DLiteFilterStrategy:
    """Filter that removes all but specified instances in the collection.

    The `query` configuration should be a regular expression matching labels
    to keep in the collection.  All other labels will be removed.

    **Registers strategies**:

    - `("filterType", "dlite/filter")`

    """

    filter_config: DLiteFilterConfig

    def initialize(
        self,
        session: "Optional[dict[str, Any]]" = None,
    ) -> DLiteSessionUpdate:
        """Initialize."""
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)

    def get(
        self, session: "Optional[dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Execute the strategy."""
        # pylint: disable=too-many-branches
        config = self.filter_config.configuration

        # Alias for query configuration
        keep_label = (
            config.keep_label if config.keep_label else self.filter_config.query
        )

        instdict = {}  # Map instance labels to [uuid, metaURI]
        coll = get_collection(session)
        for s, _, o in coll.get_relations(p="_has-uuid"):
            instdict[s] = [o]
        for s, _, o in coll.get_relations(p="_has-meta"):
            instdict[s].append(o)

        removal = set()  # Labels marked for removal

        # 1: remove_label, remove_datamodel
        if config.remove_label or config.remove_datamodel:
            for label, (_, metauri) in instdict.items():
                if config.remove_label and re.match(config.remove_label, label):
                    removal.add(label)

                if config.remove_datamodel and re.match(
                    config.remove_datamodel, metauri
                ):
                    removal.add(label)
        else:
            removal.update(instdict.keys())

        # 2: keep_label, keep_datamodel
        for label in set(removal):
            if keep_label and re.match(keep_label, label):
                removal.remove(label)

            _, metauri = instdict[label]
            if config.keep_datamodel and re.match(
                config.keep_datamodel, metauri
            ):
                removal.remove(label)

        # 3: keep_referred
        if config.keep_referred:
            labels = {uuid: label for label, (uuid, _) in instdict.items()}
            kept = set(instdict.keys()).difference(removal)
            for label in kept:
                removal.difference_update(
                    labels[inst.uuid]
                    for inst in get_referred_instances(coll.get(label))
                    if inst.uuid in labels
                )

        # 4: remove from collection
        for label in removal:
            coll.remove(label)

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)
