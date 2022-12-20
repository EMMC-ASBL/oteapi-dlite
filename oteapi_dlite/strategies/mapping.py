"""Mapping filter strategy."""
# pylint: disable=unused-argument,invalid-name
from typing import TYPE_CHECKING, Dict, Optional

import dlite
from oteapi.models import AttrDict, MappingConfig
from pydantic import AnyUrl
from pydantic.dataclasses import Field, dataclass
from tripper import Triplestore

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import (
    DLiteGlobalConfiguration,
    get_collection,
    update_collection,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class DLiteMappingStrategyConfig(AttrDict):
    """Configuration for a DLite mapping filter."""

    datamodel: Optional[AnyUrl] = Field(
        None,
        description="URI of the datamodel that is mapped.",
    )
    global_configuration_additions: DLiteGlobalConfiguration = Field(
        DLiteGlobalConfiguration(),
        description=(
            "Global DLite configuration options to append. "
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
    ) -> DLiteSessionUpdate:
        """Initialize strategy."""
        config = self.mapping_config.configuration

        for addition in config.global_configuration_additions.storage_path:
            dlite.storage_path.append(addition)
        for (
            addition
        ) in config.global_configuration_additions.storage_plugin_path:
            dlite.storage_plugin_path.append(addition)
        for (
            addition
        ) in config.global_configuration_additions.mapping_plugin_path:
            dlite.mapping_plugin_path.append(addition)
        for (
            addition
        ) in config.global_configuration_additions.python_storage_plugin_path:
            dlite.python_storage_plugin_path.append(addition)
        for (
            addition
        ) in config.global_configuration_additions.python_mapping_plugin_path:
            dlite.python_mapping_plugin_path.append(addition)

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
