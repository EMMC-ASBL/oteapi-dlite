"""RDF serialisation of OTEAPI data documentation using EMMO."""

import re
from typing import TYPE_CHECKING

from tripper import (
    DCAT,
    DCTERMS,
    MAP,
    OTEIO,
    RDF,
    RDFS,
    XSD,
    Literal,
    Namespace,
    Triplestore,
)
from tripper.errors import NamespaceError
from tripper.utils import parse_literal

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Sequence


EMMO = Namespace(
    iri="https://w3id.org/emmo#",
    label_annotations=True,
    check=True,
)

# Known IRIs
_IRIS = {
    "downloadUrl": DCAT.downloadUrl,
    "mediaType": DCAT.mediaType,
    "accessUrl": DCAT.accessUrl,
    "accessService": DCAT.accessService,
    "keyword": DCAT.keyword,
    "license": DCTERMS.license,
    "accessRights": DCTERMS.accessRights,
    "publisher": DCTERMS.publisher,
    "description": DCTERMS.description,
    "creator": DCTERMS.creator,
    "contributor": DCTERMS.contributor,
    "title": DCTERMS.title,
    "available": DCTERMS.available,
    "bibliographicCitation": DCTERMS.bibliographicCitation,
    "conformsTo": DCTERMS.conformsTo,
    "created": DCTERMS.created,
    "references": DCTERMS.references,
    "isReplacedBy": DCTERMS.isReplacedBy,
    "requires": DCTERMS.requires,
    "label": RDFS.label,
    "comment": RDFS.comment,
    "mapsTo": MAP.mapsTo,
    "dataresource": OTEIO.DataResourceStrategy,
    #
    # Add these data properties to OTEIO
    "parse": OTEIO.hasParseStrategy,
    "generate": OTEIO.hasGenerateStrategy,
    "mapping": OTEIO.hasMappingStrategy,
    "function": OTEIO.hasFunctionStrategy,
    "transformation": OTEIO.hasTransformationStrategy,
    "configuration": OTEIO.hasConfiguration,
}

# Regular expression matching a prefixed IRI
_MATCH_PREFIXED_IRI = re.compile(
    r"^([a-z][a-z0-9]*):([a-zA-Z_][a-zA-Z0-9_+-]*)$"
)
_MATCH_ANYURI = re.compile(r"^([a-z][a-z0-9]*)://(.*)$")


def save(
    ts: Triplestore,
    data_resources: dict,
    prefixes: "Optional[dict]" = None,
    version: str = "1.0",
):
    """Save a OTEAPI dict representation of a data resource to triplestore.

    Arguments:
        ts: Triplestore to save to.
        data_resources: OTEAPI dict representation of the data resources
            to save.
        prefixes: Namespace prefixes.
        version: Version number.
    """
    ts.bind("oteio", OTEIO)
    ts.bind("emmo", EMMO)
    if prefixes:
        for prefix, ns in prefixes.items():
            ts.bind(prefix, ns)

    ts.add_triples(
        to_triples(data_resources, prefixes=prefixes, version=version)
    )


def expand_iri(iri: str, prefixes: dict):
    """Return the full IRI if `iri` is prefixed.  Otherwise `iri` is
    returned."""
    match = re.match(_MATCH_PREFIXED_IRI, iri)
    if match:
        prefix, name = match.groups()
        if prefix not in prefixes:
            raise NamespaceError(f"unknown namespace: {prefix}")
        return f"{prefixes[prefix]}{name}"
    return iri


def to_triples(
    data_resources: dict,
    prefixes: "Optional[dict]" = None,
    version: str = "1.0",  # pylint: disable=unused-argument
) -> list:
    """Returns OTEAPI dict representation of a data resource as a list
    of RDF triples.

    Arguments:
        data_resources: OTEAPI dict representation of the data resources
            to save.
        prefixes: Namespace prefixes.
        version: Version number.

    Returns:
        List of RDF-triples.
    """
    # pylint: disable=too-many-locals,too-many-nested-blocks,too-many-branches
    if prefixes is None:
        prefixes = {}

    iris = set()
    triples = []
    for iri, pipeline in data_resources.items():
        iri = expand_iri(iri, prefixes)

        # Should be explicit with context strategy
        triples.append((iri, RDF.type, EMMO.DataSet))

        prev_siri = None
        for strategy in pipeline:
            for filtertype, conf in strategy.items():
                n = 1
                while f"{iri}_{filtertype}{n}" in iris:
                    n += 1
                siri = f"{iri}_{filtertype}{n}"
                iris.add(siri)

                # Special case, should be replaced with context strategy
                if filtertype == "dataresource" and "type" in conf:
                    conf = conf.copy()
                    triples.append(
                        (iri, RDF.type, expand_iri(conf.pop("type"), prefixes))
                    )

                for k, v in conf.items():
                    if isinstance(v, str):
                        if re.match(_MATCH_PREFIXED_IRI, v):
                            obj = expand_iri(v, prefixes)
                        elif re.match(_MATCH_ANYURI, v):
                            obj = Literal(v, datatype=XSD.anyURI)
                        else:
                            obj = parse_literal(v)

                    else:
                        obj = parse_literal(v)
                    triples.append((siri, _IRIS[k], obj))

                triples.append((siri, RDF.type, OTEIO.Strategy))
                triples.append((iri, EMMO.hasPart, siri))
                if prev_siri:
                    triples.append((prev_siri, EMMO.hasNext, siri))
                else:
                    triples.append((iri, EMMO.hasBeginTile, siri))
                prev_siri = siri

    return triples
