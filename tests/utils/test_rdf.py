"""Test RDF serialisation."""

# pylint: disable=unused-variable


if True:
    # def test_to_triples():
    """Test to_triples()."""

    import dlite
    import yaml
    from paths import datamodeldir, inputdir, outputdir
    from tripper import Triplestore

    from oteapi_dlite.utils import save, to_triples

    dlite.storage_path.append(datamodeldir)

    with open(inputdir / "dataresources.yaml", "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)

    data_resources = d["data_resources"]
    prefixes = d["prefixes"]
    version = d["version"]
    triples = to_triples(data_resources, prefixes=prefixes, version=version)

    ts = Triplestore("rdflib")
    save(ts, data_resources, prefixes=prefixes, version=version)
    ts.serialize(outputdir / "dataresources.ttl")

    # from tripper import OWL, RDF
    # ts.add_triples(
    #     [
    #         ("http://open-model.eu/ontologies/ss3kb", RDF.type, OWL.Ontology),
    #         ("http://open-model.eu/ontologies/ss3kb", OWL.imports, "http://open-model.eu/ontologies/ss3"),
    #     ]
    # )

    import json

    import rdflib

    data = """
    {
      "@context": {
        "prefixes": {
          "ss3": "https://w3id.org/emmo/application/ss3",
          "ss3kb": "https://w3id.org/emmo/application/ss3kb",
          "oteio": "https://w3id.org/emmo/application/oteio"
        },
        "data_resources": {
          "@id": "https://w3id.org/emmo/domain/oteio#DataResource",
          "@container": "@list"
        },
        "filters": {
          "@id": "https://w3id.org/emmo/domain/oteio#Filter",
          "@container": "@list"
        }
      },

      "data_resources": [
        {
          "@id": "ss3kb:aa6082",
          "@type": "ss3:ReinforcementMaterialCard",
          "filters": [
            {
              "@type": "oteio:DataResource"
            }
          ]
        }
      ]
    }
    """

    # Check syntax
    json.loads(data)
