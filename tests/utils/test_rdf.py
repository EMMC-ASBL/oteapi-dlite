"""Test RDF serialisation."""

import yaml
from paths import inputdir, outputdir
from tripper import Triplestore

from oteapi_dlite.utils import save, to_triples

# pylint: disable=unused-variable


# if True:
def test_to_triples():
    """Test to_triples()."""
    with open(inputdir / "dataresources.yaml", "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)

    data_resources = d["data_resources"]
    prefixes = d["prefixes"]
    version = d["version"]
    triples = to_triples(data_resources, prefixes=prefixes, version=version)

    ts = Triplestore("rdflib")
    save(ts, data_resources, prefixes=prefixes, version=version)
    ts.serialize(outputdir / "dataresources.ttl")
