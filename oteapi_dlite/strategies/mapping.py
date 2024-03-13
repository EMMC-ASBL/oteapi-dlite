"""Mapping filter strategy."""

# pylint: disable=unused-argument,invalid-name
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Optional

from oteapi.models import AttrDict, MappingConfig
from pydantic import AnyUrl
from pydantic.dataclasses import Field, dataclass
from tripper import Triplestore

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class BackendEnum(str, Enum):
    """
    Defines the currently available triplestore backends
    """

    fuseki = "fuseki"
    stardog = "stardog"
    graphdb = "graphdb"


class DLiteMappingStrategyConfig(AttrDict):
    """Configuration for a DLite mapping filter."""

    datamodel: Annotated[
        Optional[AnyUrl],
        Field(
            description="URI of the datamodel that is mapped.",
        ),
    ] = None
    collection_id: Annotated[
        Optional[str], Field(description="A reference to a DLite collection.")
    ] = None
    backend: Annotated[
        Optional[BackendEnum],
        Field(
            description=(
                "Specifies the triplestore backend to be used."
                "Options include 'fuseki', 'stardog', and 'graphdb'"
            )
        ),
    ] = None
    base_iri: Annotated[
        Optional[str],
        Field(
            description=(
                "The base IRI used as a starting point for generating IRIs for "
                "the resources in the mapping process."
            )
        ),
    ] = None
    triplestore_url: Annotated[
        Optional[str],
        Field(description="The URL of the triplestore service endpoint."),
    ] = None
    database: Annotated[
        Optional[str],
        Field(
            description=(
                "The name of the database within the triplestore backend."
            )
        ),
    ] = None
    username: Annotated[
        Optional[str],
        Field(
            description=(
                "The username required for authenticating with the "
                "triplestore backend, if applicable."
            )
        ),
    ] = None
    password: Annotated[
        Optional[str],
        Field(
            description=(
                "The password associated with the username for "
                "authentication purposes. "
            )
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

    def initialize(self) -> DLiteSessionUpdate:
        """Initialize strategy."""
        coll = get_collection(
            collection_id=self.mapping_config.configuration.collection_id
        )
        if self.mapping_config.configuration.backend:
            ts = Triplestore(
                backend=self.mapping_config.configuration.backend,
                base_iri=self.mapping_config.configuration.base_iri,
                triplestore_url=self.mapping_config.configuration.triplestore_url,  # pylint: disable=line-too-long
                database=self.mapping_config.configuration.database,
                uname=self.mapping_config.configuration.username,
                pwd=self.mapping_config.configuration.password,
            )
        else:
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
                    for triple in self.mapping_config.triples  # pylint: disable=not-an-iterable
                ]
            )

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)

    def get(self) -> DLiteSessionUpdate:
        """Execute strategy and return a dictionary."""
        return DLiteSessionUpdate(
            collection_id=(
                self.mapping_config.configuration.collection_id
                if self.mapping_config.configuration.collection_id
                else get_collection().uuid
            )
        )
