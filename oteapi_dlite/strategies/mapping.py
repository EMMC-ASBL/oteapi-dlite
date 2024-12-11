"""Mapping filter strategy."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated, Optional

from oteapi.models import MappingConfig
from pydantic import AnyUrl
from pydantic.dataclasses import Field, dataclass

from oteapi_dlite.models import DLiteConfiguration, DLiteResult
from oteapi_dlite.utils import (
    get_collection,
    get_triplestore,
    update_collection,
)

if TYPE_CHECKING:  # pragma: no cover
    pass


class DLiteMappingStrategyConfig(DLiteConfiguration):
    """Configuration for a DLite mapping filter."""

    datamodel: Annotated[
        Optional[AnyUrl],
        Field(
            description="URI of the datamodel that is mapped.",
        ),
    ] = None


class DLiteMappingConfig(MappingConfig):
    """DLite mapping strategy config."""

    configuration: Annotated[
        DLiteMappingStrategyConfig,
        Field(
            description="DLite mapping strategy-specific configuration.",
        ),
    ] = DLiteMappingStrategyConfig()


@dataclass
class DLiteMappingStrategy:
    """Strategy for a mapping.

    **Registers strategies**:

    - `("mappingType", "mappings")`

    """

    mapping_config: DLiteMappingConfig

    def initialize(self) -> DLiteResult:
        """Initialize strategy."""
        config = self.mapping_config.configuration

        coll = get_collection(config.collection_id)

        kb_settings = config.dlite_settings.get("tripper.triplestore")
        if isinstance(kb_settings, str):
            kb_settings = json.loads(kb_settings)
        if kb_settings and not isinstance(kb_settings, dict):
            raise ValueError(
                "The `tripper.triplestore` setting must be a dictionary."
            )

        if TYPE_CHECKING:  # pragma: no cover
            # This block will only be run by mypy when checking typing
            assert isinstance(kb_settings, dict) or kb_settings is None  # nosec

        ts = get_triplestore(kb_settings=kb_settings, collection_id=coll.uuid)

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
        return DLiteResult(collection_id=coll.uuid)

    def get(self) -> DLiteResult:
        """Execute strategy and return a dictionary."""
        return DLiteResult(
            collection_id=get_collection(
                self.mapping_config.configuration.collection_id
            ).uuid
        )
