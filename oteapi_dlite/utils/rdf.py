"""RDF serialisation of OTEAPI data documentation using EMMO."""

import io
import json
import re
import warnings

# from pathlib import Path
from typing import TYPE_CHECKING

import requests
from tripper import DCAT, OTEIO, RDF, Triplestore
from tripper.utils import as_python

# from tripper.errors import NamespaceError
# from tripper.utils import parse_literal

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, List, Mapping, Optional, Union


# Pytest can't cope with this
# EMMO = Namespace(
#     iri="https://w3id.org/emmo#",
#     label_annotations=True,
#     check=True,
# )

# CONTEXT = (
#     (Path(__file__).parent.parent / "context" / "context.json").as_uri()
# )

# __TODO__: Update URI when merged to master
CONTEXT = (
    "https://raw.githubusercontent.com/EMMC-ASBL/oteapi-dlite/refs/heads/"
    "rdf-serialisation/oteapi_dlite/context/context.json"
)

_MATCH_PREFIXED_IRI = re.compile(r"^([a-z0-9]*):([a-zA-Z_][a-zA-Z0-9_+-]*)$")

DataSet = "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a"


def save_dataset(
    ts: Triplestore,
    dataset: "Union[dict, str]",
    distribution: "Optional[Union[dict, List[dict]]]" = None,
    datasink: "Optional[Union[dict, List[dict]]]" = None,
    prefixes: "Optional[dict]" = None,
) -> dict:
    # pylint: disable=line-too-long,too-many-branches
    """Save a dict representation of dataset documentation to a triplestore.

    Arguments:
        ts: Triplestore to save to.
        dataset: A dict documenting a new dataset or an IRI referring to an
            existing dataset.

            If this is a dict, the keys may be either properties of
            [dcat:Dataset](https://www.w3.org/TR/vocab-dcat-3/#Class:Dataset)
            (without the prefix) or one of the following keywords:
              - "@id": Dataset IRI.  Must always be given.
              - "@type": IRI of a specific dataset subclass. Typically is used
                to refer to a specific subclass of `emmo:DataSet`, providing a
                semantic description of this dataset.
        distribution: A dict or a list of dicts documenting specific
            realisations of the dataset.  The keys may be either properties of
            [dcat:Distribution](https://www.w3.org/TR/vocab-dcat-3/#Class:Distribution)
            (not prefixed with a namespace) or any of the following keys:
               - "@id": Distribution IRI. Must always be given.
               - "parser": Sub-dict documenting an OTEAPI parser.
               - "mapping": Sub-dict documenting OTEAPI mappings.
        datasink: A dict or a list of dicts documenting specific  sink for this
            dataset.
        prefixes: Namespace prefixes that should be recognised as values.

    Returns:
        Updated copy of `dataset`.

    SeeAlso:
        __TODO__: add URL to further documentation and examples.
    """
    if isinstance(dataset, str):
        dataset = load_dataset(ts, dataset)
    else:
        dataset = dataset.copy()

    if "@id" not in dataset:
        raise ValueError("dataset must have an '@id' key")

    add(dataset, "@context", CONTEXT)

    # Add distribution and datasink
    for k, v, type_ in [
        ("distribution", distribution, DCAT.Distribution),
        ("datasink", datasink, OTEIO.DataSink),
    ]:
        if v:
            add(dataset, k, v)
        if k in dataset:
            if isinstance(dataset[k], list):
                for d in dataset[k]:
                    add(d, "@type", type_)
            else:
                add(dataset[k], "@type", type_)

    # Expand prefixes
    _expand_prefixes(dataset, prefixes if prefixes else {})

    # Append dcat:Dataset to @type
    add(dataset, "@type", DCAT.Dataset)

    # Bind prefixes
    default_prefixes = {
        "adms": "http://www.w3.org/ns/adms#",
        "dcat": "http://www.w3.org/ns/dcat#",
        "dcterms": "http://purl.org/dc/terms/",
        "dctype": "http://purl.org/dc/dcmitype/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "odrl": "http://www.w3.org/ns/odrl/2/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "prov": "http://www.w3.org/ns/prov#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "schema": "http://schema.org/",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "spdx": "http://spdx.org/rdf/terms#",
        "vcard": "http://www.w3.org/2006/vcard/ns#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "emmo": "https://w3id.org/emmo#",
        "oteio": "https://w3id.org/emmo/domain/oteio#",
    }
    if prefixes:
        default_prefixes.update(prefixes)
    for prefix, ns in default_prefixes.items():
        ts.bind(prefix, ns)

    # Write json-ld data to temporary rdflib triplestore
    f = io.StringIO(json.dumps(dataset))
    ts2 = Triplestore(backend="rdflib")
    ts2.parse(f, format="json-ld")

    # Add triples from temporary triplestore
    ts.add_triples(ts2.triples())

    ts2.close()  # explicit close ts2

    return dataset


def load_dataset(ts: Triplestore, iri: str) -> dict:
    """Load dataset from triplestore.

    Arguments:
        ts: Triplestore to load dataset from.
        iri: IRI of the dataset to load.

    Returns:
        Dict-representation of the loaded dataset.
    """
    if CONTEXT.startswith("file://"):
        with open(CONTEXT[7:], "r", encoding="utf-8") as f:
            context = json.load(f)["@context"]
    else:
        r = requests.get(CONTEXT, allow_redirects=True, timeout=3)
        context = json.loads(r.content)["@context"]

    print("*** context", context)

    shortnames = {
        ts.expand_iri(v): k
        for k, v in context.items()
        if isinstance(v, str) and not v.endswith(("#", "/"))
    }
    shortnames.setdefault(RDF.type, "@type")
    shortnames.setdefault(OTEIO.prefix, "prefixes")
    shortnames.setdefault(OTEIO.hasConfiguration, "configuration")
    shortnames.setdefault(OTEIO.statement, "statement")

    dataset: dict = {}
    for p, o in ts.predicate_objects(ts.expand_iri(iri)):
        add(dataset, shortnames.get(p, p), as_python(o))
    _update_dataset(ts, iri, dataset, context, shortnames)
    add(dataset, "@id", iri)

    return dataset


def _update_dataset(
    ts: Triplestore, iri: str, dct: dict, context: dict, shortnames: dict
) -> None:
    """Recursively update dict-representation of dataset."""
    nested = ("distribution", "datasink", "parser", "generator", "mapping")

    for name in nested:
        if name in dct:
            v = dct[name] if isinstance(dct[name], list) else [dct[name]]
            for i, node in enumerate(v):
                d: dict = {}
                for p, o in ts.predicate_objects(ts.expand_iri(node)):
                    add(d, shortnames.get(p, p), as_python(o))
                if isinstance(dct[name], list):
                    dct[name][i] = d
                else:
                    dct[name] = d
                _update_dataset(ts, node, d, context, shortnames)

            # if isinstance(dct[name], list):
            #    for i, node in enumerate(dct[name]):
            #        d = {}
            #        for p, o in ts.predicate_objects(ts.expand_iri(node)):
            #            add(d, shortnames.get(p, p), as_python(o))
            #        dct[name][i] = d
            #        _update_dataset(ts, node, d, context, shortnames)
            # else:
            #    d = {}
            #    for p, o in ts.predicate_objects(ts.expand_iri(dct[name])):
            #        add(d, shortnames.get(p, p), as_python(o))
            #    dct[name] = d
            #    _update_dataset(ts, name, d, context, shortnames)

    if "statement" in dct:
        (iri,) = ts.objects(predicate=OTEIO.statement)
        dct["statement"] = load_statements(ts, iri)


def load_list(ts: Triplestore, iri: str):
    """Load and return RDF list whos first node is `iri`."""
    lst = []
    for p, o in ts.predicate_objects(iri):
        if p == RDF.first:
            lst.append(o)
        elif p == RDF.rest:
            lst.extend(load_list(ts, o))
    return lst


def load_statements(ts: Triplestore, iri: str):
    """Load and return list of spo statements from triplestore, with `iri`
    being the first node in the list of statements.
    """
    statements = []
    for node in load_list(ts, iri):
        d = {}
        for p, o in ts.predicate_objects(node):
            if p == RDF.subject:
                d["subject"] = as_python(o)
            elif p == RDF.predicate:
                d["predicate"] = as_python(o)
            elif p == RDF.object:
                d["object"] = as_python(o)
        statements.append(d)
    return sorted(statements, key=lambda d: sorted(d.items()))


def add(d: dict, key: str, value: "Any") -> None:
    """Append key-value pair to dict `d`.

    If `key` already exists in `d`, its value is converted to a list and
    `value` is appended to it.  Values are not duplicated.
    """
    if key not in d:
        d[key] = value
    else:
        klst = d[key] if isinstance(d[key], list) else [d[key]]
        vlst = value if isinstance(value, list) else [value]
        v = list(set(klst).union(vlst))
        d[key] = v[0] if len(v) == 1 else sorted(v)


def _expand_prefixes(d: dict, prefixes: dict) -> None:
    """Recursively expand IRI prefixes in the values of dict `d`."""
    for k, v in d.items():
        if isinstance(v, str):
            d[k] = expand_iri(v, prefixes)
        elif isinstance(v, list):
            _expand_elements(v, prefixes)
        elif isinstance(v, dict):
            _expand_prefixes(v, prefixes)


def _expand_elements(lst: list, prefixes: dict) -> None:
    """Recursively expand IRI prefixes in the elements of list `lst`."""
    for i, e in enumerate(lst):
        if isinstance(e, str):
            lst[i] = expand_iri(e, prefixes)
        elif isinstance(e, list):
            _expand_elements(e, prefixes)
        elif isinstance(e, dict):
            _expand_prefixes(e, prefixes)


def expand_iri(iri: str, prefixes: dict) -> str:
    """Return the full IRI if `iri` is prefixed.  Otherwise `iri` is
    returned."""
    match = re.match(_MATCH_PREFIXED_IRI, iri)
    if match:
        prefix, name = match.groups()
        if prefix in prefixes:
            return f"{prefixes[prefix]}{name}"
        warnings.warn(f'Undefined prefix "{prefix}" in IRI: {iri}')
    return iri
