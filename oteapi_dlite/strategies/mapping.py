"""Mapping filter strategy."""
# pylint: disable=unused-argument,invalid-name
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import dlite
from oteapi.models import AttrDict, MappingConfig, SessionUpdate
from pydantic.dataclasses import Field, dataclass
from tripper import Triplestore

from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class DLiteMappingStrategyConfig(AttrDict):
    """Configuration for a DLite mapping filter."""

    datamodel: Optional[str] = Field(
        None,
        description="URI of the datamodel that is mapped.",
    )
    global_configuration_additions: Dict[str, Union[str, List[str]]] = Field(
        {},
        description=(
            "A dictionary of DLite global configuration options to append. "
            "E.g., `storage_path` or `python_storage_plugin_path`."
        ),
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
    ) -> "SessionUpdate":
        """Initialize strategy."""
        if session is None:
            raise ValueError("Missing session")

        config = self.mapping_config.configuration

        for (
            dlite_global_config,
            additions,
        ) in config.global_configuration_additions.items():
            if not hasattr(dlite, dlite_global_config):
                raise ValueError(
                    f"{dlite_global_config!r} is not a valid DLite global "
                    "configuration name."
                )
            if isinstance(additions, str):
                additions = [additions]
            setattr(
                dlite,
                dlite_global_config,
                getattr(dlite, dlite_global_config, []).extend(additions),
            )

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
        return SessionUpdate()

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "SessionUpdate":
        """Execute strategy and return a dictionary."""
        return SessionUpdate()
