"""Mapping filter strategy."""

from __future__ import annotations

import logging

# pylint: disable=unused-argument,invalid-name,disable=line-too-long,E1133,W0511
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Optional

import rdflib
from jinja2 import Template, TemplateError
from oteapi.models import AttrDict, MappingConfig
from pydantic import AnyUrl
from pydantic.dataclasses import Field, dataclass
from rdflib.exceptions import Error as RDFLibException
from SPARQLWrapper import JSON, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
from tripper import Triplestore

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any
logger = logging.getLogger(__name__)


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
    graph_uri: Annotated[
        Optional[str],
        Field(
            description=("The URI of the graph in which to perform the query")
        ),
    ] = None
    sparql_endpoint: Annotated[
        Optional[str],
        Field(
            description="Endpoint Url to create an instance of SPARQLWrapper configured for the target SPARQL service"
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
                triplestore_url=self.mapping_config.configuration.triplestore_url,
                database=self.mapping_config.configuration.database,
                uname=self.mapping_config.configuration.username,
                pwd=self.mapping_config.configuration.password,
            )
        else:
            ts = Triplestore(backend="collection", collection=coll)

        if self.mapping_config.prefixes:
            for prefix, iri in self.mapping_config.prefixes.items():
                ts.bind(prefix, iri)
        if (
            self.mapping_config.configuration.sparql_endpoint
            and self.mapping_config.configuration.graph_uri
        ):
            config = self.mapping_config.configuration
            sparql_instance = SPARQLWrapper(config.sparql_endpoint)
            sparql_instance.setHTTPAuth("BASIC")
            sparql_instance.setCredentials(
                config.username,
                config.password,
            )
            # extract class names i.e. objects from triples
            class_names = [triple[2] for triple in self.mapping_config.triples]
            # Find parent node of the class_names
            parent_node: str | None = find_parent_node(
                sparql_instance,
                class_names,
                config.graph_uri,  # type:ignore
            )
            # If parent node exists, find the KG
            if parent_node:
                graph: rdflib.Graph = fetch_and_populate_graph(
                    sparql_instance,
                    config.graph_uri,  # type:ignore
                    parent_node,
                )
                graph_triples = [(str(s), str(p), str(o)) for s, p, o in graph]
                # Add triples to the collection
                populate_triplestore(ts, graph_triples)

        # Add triples to the collection
        populate_triplestore(ts, self.mapping_config.triples)
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


def populate_triplestore(ts: Triplestore, triples: list):
    """Populate the triplestore instance"""
    ts.add_triples(
        [
            [ts.expand_iri(t) if isinstance(t, str) else t for t in triple]
            for triple in (triples)  # pylint: disable=not-an-iterable
        ]
    )


# TODO: import the below function from SOFT7 once its available
def find_parent_node(
    sparql: SPARQLWrapper,
    class_names: list[str],
    graph_uri: str,
) -> str | None:
    """
    Queries a SPARQL endpoint to find a common parent node (LCA) for a given list of
    class URIs within a specified RDF graph.

    Args:
        sparql (SPARQLWrapper): An instance of SPARQLWrapper configured for the target
            SPARQL service.
        class_names (list[str]): The class URIs to find a common parent for.
        graph_uri (str): The URI of the graph in which to perform the query.

    Returns:
        str | None: The URI of the common parent node if one exists, otherwise None.

    Raises:
        RuntimeError: If there is an error in executing or processing the SPARQL query
            or if there is an error in rendering the SPARQL query using Jinja2 templates.

    Note:
        This function assumes that the provided `sparql` instance is already configured
            with necessary authentication and format settings.
    """

    try:
        template_str = """
        {% macro sparql_query(class_names, graph_uri) %}
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?parentClass
            WHERE {
                GRAPH <{{ graph_uri }}> {
                    ?class rdfs:subClassOf* ?parentClass .
                    FILTER(
                        {% for class_name in class_names -%}
                            ?class = <{{ class_name }}>{{ " ||" if not loop.last }}
                        {% endfor %})
                }
            }
        {% endmacro %}
        """

        template = Template(template_str)
        query = template.module.sparql_query(class_names, graph_uri)
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)

        target_count = len(class_names)
        counts: dict[str, int] = {}

        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            parent_class = result["parentClass"]["value"]
            counts[parent_class] = counts.get(parent_class, 0) + 1
            if counts[parent_class] == target_count:
                return parent_class

    except SPARQLWrapperException as wrapper_error:
        raise RuntimeError(
            f"Failed to fetch or parse results: {wrapper_error}"
        ) from wrapper_error

    except TemplateError as template_error:
        raise RuntimeError(
            f"Jinja2 template error: {template_error}"
        ) from template_error

    logger.info("Could not find a common parent node.")
    return None


# TODO: import the below function from SOFT7 once its available
def fetch_and_populate_graph(
    sparql: SPARQLWrapper,
    graph_uri: str,
    parent_node: str,
    graph: Optional[rdflib.Graph] = None,
) -> rdflib.Graph | None:
    """
    Fetches RDF triples related to a specified parent node from a SPARQL endpoint and
    populates them into an RDF graph.

    Args:
        sparql (SPARQLWrapper): An instance of SPARQLWrapper configured for the target
            SPARQL service.
        graph_uri (str): The URI of the graph from which triples will be fetched.
        parent_node (str): The URI of the parent node to base the triple fetching on.
        graph (rdflib.Graph, optional): An instance of an RDFlib graph to populate with
            fetched triples.
            If `None`, a new empty graph is created. Defaults to `None`.

    Returns:
        rdflib.Graph: The graph populated with the fetched triples.

    Raises:
        RuntimeError: If processing the SPARQL query or building the RDF graph fails.

    Note:
        This function assumes that the provided `sparql` instance is already configured
            with necessary authentication and format settings.
    """
    # Create a new graph if one is not provided
    graph = graph or rdflib.Graph()

    try:
        sparql.setReturnFormat(JSON)

        query = f"""
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX fno: <https://w3id.org/function/ontology#>
        PREFIX emmo: <http://emmo.info/domain-mappings#>
        PREFIX oteio: <http://emmo.info/oteio#>

        SELECT DISTINCT ?subject ?predicate ?object
        WHERE {{
        GRAPH <{graph_uri}> {{

            # Match all subclasses of the parent class
            ?subclass rdfs:subClassOf* <{parent_node}> .

            # Retrieve all relevant triples for these subclasses and their individuals
            {{
            # Subclasses themselves and their relationships
            ?subclass ?predicate ?object .
            BIND(?subclass AS ?subject)
            }} UNION {{
            # Individuals of these subclasses and their properties
            ?subject rdf:type ?subclass .
            ?subject ?predicate ?object .
            }}

            # Ensure subject, predicate, and object are not empty
            FILTER(BOUND(?subject) && BOUND(?predicate) && BOUND(?object))

            # Filter by the specific predicates
            FILTER (?predicate IN (
                rdfs:subClassOf,
                rdfs:label,
                rdf:type,
                rdf:about,
                owl:propertyDisjointWith,
                fno:expects,
                fno:predicate,
                fno:type,
                fno:returns,
                fno:executes,
                oteio:hasPythonFunctionName,
                oteio:hasPythonModuleName,
                oteio:hasPypiPackageName,
                emmo:mapsTo))
        }}
        }}
        """
        sparql.setQuery(query)

        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            graph.add(
                (
                    rdflib.URIRef(result["subject"]["value"]),
                    rdflib.URIRef(result["predicate"]["value"]),
                    rdflib.URIRef(result["object"]["value"]),
                )
            )
        logger.info("Graph populated with fetched triples.")

    except SPARQLWrapperException as wrapper_error:
        raise RuntimeError(
            f"Failed to fetch or parse results: {wrapper_error}"
        ) from wrapper_error

    except RDFLibException as rdflib_error:
        raise RuntimeError(
            f"Failed to build graph elements: {rdflib_error}"
        ) from rdflib_error

    return graph
