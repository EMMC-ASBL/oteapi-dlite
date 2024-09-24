"""Test RDF serialisation."""


# if True:
def test_save_and_load_dataset():
    """Test save_dataset() and load_dataset()."""

    # from paths import inputdir, outputdir
    from tripper import Triplestore

    from oteapi_dlite.utils import load_dataset, save_dataset

    dataset = {
        "@id": "ex:mydata",
        "@type": "ex:MyData",
        "title": "My data.",
        "distribution": {
            "downloadURL": (
                "https://raw.githubusercontent.com/H2020-OpenModel/"
                "Public/SS3_data/data/SS3/material_card_al.json"
            ),
            "mediaType": "application/json",
            "parser": {
                "parserType": "application/vnd.dlite-parse",
                "datamodel": "http://onto-ns.com/meta/ss3/0.1/MyData",
                "configuration": {"driver": "json", "options": ""},
                "mapping": {
                    "prefixes": {
                        "aa": "http://aa.org#",
                        "bb": "http://bb.org#",
                    },
                    "statement": [
                        {"subject": "a", "predicate": "b", "object": "c"},
                        {"subject": "d", "predicate": "e", "object": "f"},
                    ],
                },
            },
        },
    }

    prefixes = {
        "ex": "http://example.com#",
    }

    # Store dict representation of the dataset to triplestore
    ts = Triplestore("rdflib")
    ds = save_dataset(ts, dataset, prefixes=prefixes)
    repr1 = set(ts.triples())

    # Load back dict representation from the triplestore
    EX = ts.namespaces["ex"]
    d = load_dataset(ts, iri=EX.mydata)

    # Store the new dict representation to another triplestore
    ts2 = Triplestore("rdflib")
    ds2 = save_dataset(ts2, d)
    repr2 = set(ts.triples())

    # Ensure that both dict and triplestore representations are equal
    assert ds2 == ds
    assert repr2 == repr1
