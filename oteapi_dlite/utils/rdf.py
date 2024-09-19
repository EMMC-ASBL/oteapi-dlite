"""RDF serialisation of OTEAPI data documentation using EMMO."""

import re
from typing import TYPE_CHECKING

from tripper import (
    DCAT,
    DCTERMS,
    EMMO,
    MAP,
    OTEIO,
    RDF,
    RDFS,
    XSD,
    Literal,
    Triplestore,
)
from tripper.errors import NamespaceError
from tripper.utils import parse_literal

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Sequence


# Pytest can't cope with this
# EMMO = Namespace(
#     iri="https://w3id.org/emmo#",
#     label_annotations=True,
#     check=True,
# )

emmo_DataSet = "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a"

# Known IRIs
_IRIS = {
    "downloadUrl": DCAT.downloadURL,
    "mediaType": DCAT.mediaType,
    "accessUrl": DCAT.accessURL,
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
    #
    # Add these data properties to OTEIO
    "dataresource": OTEIO.hasDataResourceFilter,
    "parse": OTEIO.hasParseFilter,
    "generate": OTEIO.hasGenerateFilter,
    "mapping": OTEIO.hasMappingFilter,
    "function": OTEIO.hasFunctionFilter,
    "transformation": OTEIO.hasTransformationFilter,
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
        triples.append((iri, RDF.type, emmo_DataSet))

        prev_firi = None
        for filter in pipeline:  # pylint: disable=redefined-builtin
            for filtertype, conf in filter.items():
                n = 1
                while f"{iri}_{filtertype}{n}" in iris:
                    n += 1
                firi = f"{iri}_{filtertype}{n}"
                iris.add(firi)

                # Special case, should be replaced with context strategy
                if filtertype == "dataresource":
                    triples.append((firi, RDF.type, DCAT.Distribution))
                    triples.append((iri, DCAT.distribution, firi))
                    if "type" in conf:
                        conf = conf.copy()
                        obj = expand_iri(conf.pop("type"), prefixes)
                        triples.append((iri, RDF.type, obj))
                        triples.append((iri, RDF.type, DCAT.Dataset))

                    ### Add datasets...
                    if False:
                        import dlite
                        from dlite.dataset import metadata_to_rdf

                        c = conf["configuration"]
                        dm = c["datamodel"]
                        meta = dlite.get_instance(dm)
                        triples.extend(metadata_to_rdf(meta))
                        triples.append((iri, RDF.type, dm))

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
                    triples.append((firi, _IRIS[k], obj))

                # triples.append((iri, OTEIO.hasFilter, firi))
                triples.append((firi, RDF.type, OTEIO.Filter))
                triples.append((firi, OTEIO.filterType, Literal(filtertype)))
                if prev_firi:
                    triples.append((prev_firi, OTEIO.hasNextFilter, firi))
                else:
                    triples.append((iri, OTEIO.hasBeginFilter, firi))
                prev_firi = firi

    return triples
