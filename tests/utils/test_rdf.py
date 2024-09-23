"""Test RDF serialisation."""

# pylint: disable=unused-variable,line-too-long


# if True:
def test_to_triples():
    """Test to_triples()."""

    import json

    # from paths import inputdir, outputdir
    from tripper import Triplestore

    from oteapi_dlite.utils import load_dataset, save_dataset

    data = """
    {
      "@context": "file:///home/friisj/prosjekter/EMMC/OntoTrans/oteapi-dlite/oteapi_dlite/context/context.json",
      "dataset": [
        {
          "@id": "http://open-model.eu/ontologies/ss3kb#aa6082",
          "@type": [
              "http://www.w3.org/ns/dcat#Dataset",
              "http://open-model.eu/ontologies/ss3#ReinforcementMaterialCard"
          ],
          "title": "My data.",
          "distribution": {
            "downloadURL": "https://raw.githubusercontent.com/H2020-OpenModel/Public/SS3_data/data/SS3/material_card_al.json",
            "mediaType": "application/json",
            "parser": {
              "datamodel": "http://onto-ns.com/meta/ss3/0.1/MyData",
              "mapping": {
                "statement": [
                  {
                    "subject": "a",
                    "predicate": "b",
                    "object": "c"
                  },
                  {
                    "subject": "d",
                    "predicate": "e",
                    "object": "f"
                  }
                ]
              }
            }
          }
        }
      ]
    }
    """

    # Check syntax
    json.loads(data)

    # f = io.StringIO(data)
    # ts = Triplestore("rdflib")
    # ts.parse(f, format="json-ld")
    # print(ts.serialize())

    dataset = {
        "@id": "ex:mydata",
        "@type": "ex:MyData",
        "title": "My data.",
        "distribution": {
            "downloadURL": "https://raw.githubusercontent.com/H2020-OpenModel/Public/SS3_data/data/SS3/material_card_al.json",
            "mediaType": "application/json",
            "parser": {
                "datamodel": "http://onto-ns.com/meta/ss3/0.1/MyData",
                "mapping": {
                    "statement": [
                        {"subject": "a", "predicate": "b", "object": "c"},
                        {"subject": "d", "predicate": "e", "object": "f"},
                    ]
                },
            },
        },
    }

    prefixes = {
        "ex": "http://example.com#",
    }

    ts = Triplestore("rdflib")
    ds = save_dataset(ts, dataset, prefixes=prefixes)
    print("------------------------")
    print(ts.serialize())

    EX = ts.namespaces["ex"]
    d = load_dataset(ts, iri=EX.mydata)
    print("------------------------")
    print(d)

    # rdflib.Graph.serialize(format="json-ld") is unreadable!
    # Use self-implemented serialiser...
    # print("------------------------")
    # print(ts.serialize(format="json-ld"))
