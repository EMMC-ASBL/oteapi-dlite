"""Mapping filter strategy."""
# pylint: disable=unused-argument,invalid-name
from typing import TYPE_CHECKING, Optional

from oteapi.models import AttrDict, MappingConfig
from pydantic import AnyUrl
from pydantic.dataclasses import Field, dataclass
from tripper import Triplestore

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict


class DLiteMappingStrategyConfig(AttrDict):
    """Configuration for a DLite mapping filter."""

    datamodel: Optional[AnyUrl] = Field(
        None,
        description="URI of the datamodel that is mapped.",
    )


class DLiteMappingConfig(MappingConfig):
    """DLite mapping strategy config."""

    configuration: DLiteMappingStrategyConfig = Field(
        DLiteMappingStrategyConfig(),
        description="DLite mapping strategy-specific configuration.",
    )


@dataclass
class DLiteMappingStrategy:
    """Strategy for a mapping.

    **Registers strategies**:

    - `("mappingType", "mappings")`

    """

    mapping_config: DLiteMappingConfig

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Initialize strategy."""
        coll = get_collection(session)
        ts = Triplestore(backend="collection", collection=coll)

        if self.mapping_config.prefixes:
            for prefix, iri in self.mapping_config.prefixes.items():
                ts.bind(prefix, iri)

        if self.mapping_config.triples:
            ts.add_triples(
                [
                    [
                        ts.expand_iri(t) if isinstance(t, str) else t
                        for t in triple
                    ]
                    for triple in self.mapping_config.triples
                ]
            )

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Execute strategy and return a dictionary."""
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)
