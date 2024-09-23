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
    # save(ts, data_resources, prefixes=prefixes, version=version)
    # ts.serialize(outputdir / "dataresources.ttl")

    # from tripper import OWL, RDF
    # ts.add_triples(
    #     [
    #         ("http://open-model.eu/ontologies/ss3kb", RDF.type, OWL.Ontology),
    #         ("http://open-model.eu/ontologies/ss3kb", OWL.imports, "http://open-model.eu/ontologies/ss3"),
    #     ]
    # )

    import io
    import json

    import rdflib

    data = """
    {
      "@context": {
        "dcat": "http://www.w3.org/ns/dcat#",
        "dcterms": "http://purl.org/dc/terms/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "ss3": "http://open-model.eu/ontologies/ss3#",
        "ss3kb": "http://open-model.eu/ontologies/ss3kb#",
        "emmo": "https://w3id.org/emmo#",
        "oteio": "https://w3id.org/emmo/domain/oteio#",

        "prefixes": {
          "@type": "oteio:prefix",
          "ss3": "http://open-model.eu/ontologies/ss3#",
          "ss3kb": "http://open-model.eu/ontologies/ss3kb#"
        },
        "datasets": {
          "@type": "dcat:DataSet",
          "keyword": "dcat:keyword",
          "title": "dcterms:title",
          "description": "dcterms:description"
        },
        "distribution": {
          "@type": "dcat:Distribution",
          "type": "https://w3id.org/emmo/domain/oteio#DataResource",
          "@container": "@list"
        },
        "parse": {
          "@type": "oteio:StructuralDocumentation",
          "datamodel": "oteio:datamodel"
        },
        "mapping": {
          "@type": "oteio:SemanticDocumentation",
          "statement": {
            "@type": "rdf:Statement",
            "@container": "@list"
          }
        }
      },

      "datasets": [
        {
          "@id": "ss3kb:aa6082",
          "@type": "ss3:ReinforcementMaterialCard",
          "distribution": {
            "@type": "oteio:DataResource",
            "title": "My data.",
            "parse": {
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

    data2 = """
    {
      "@context": "file:///home/friisj/prosjekter/EMMC/OntoTrans/oteapi-dlite/oteapi_dlite/context/context.json",
      "datasets": [
        {
          "@id": "http://open-model.eu/ontologies/ss3kb#aa6082",
          "type": "http://open-model.eu/ontologies/ss3#ReinforcementMaterialCard",
          "distribution": {
            "type": "https://w3id.org/emmo/domain/oteio#DataResource",
            "title": "My data.",
            "parse": {
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
    json.loads(data2)

    f = io.StringIO(data2)
    ts.parse(f, format="json-ld")
    print(ts.serialize())
