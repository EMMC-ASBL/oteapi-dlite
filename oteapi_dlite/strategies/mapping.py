"""Mapping filter strategy."""
# pylint: disable=unused-argument,invalid-name
from typing import TYPE_CHECKING

from oteapi.models import AttrDict, MappingConfig, SessionUpdate
from pydantic.dataclasses import Field, dataclass
from tripper import Triplestore

from oteapi_dlite.utils import get_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict, Optional

    from pydantic import AnyUrl


class Config(AttrDict):
    """Configuration for a DLite mapping filter."""

    datamodel: "AnyUrl" = Field(
        None,
        description="URI of the datamodel that is mapped.",
    )


class DLiteMappingConfig(MappingConfig):
    """DLite mapping strategy config."""

    configuration: "Optional[Config]" = Field(
        None, description="DLite mapping strategy-specific configuration."
    )


@dataclass
class DLiteMappingStrategy:
    """Strategy for a mapping.

    **Registers strategies**:

    - `("mappingType", "mappings")`

    """

    mapping_config: MappingConfig

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "SessionUpdate":
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

        return SessionUpdate()

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "SessionUpdate":
        """Execute strategy and return a dictionary."""
        return SessionUpdate()
