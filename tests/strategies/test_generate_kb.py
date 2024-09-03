"""Tests storing documentation of instance with the generate strategy."""

# pylint: disable=too-many-locals


# if True:
def test_generate_kb():
    """Test generate with kb documentation enabled."""
    # pylint: disable=too-many-statements

    from pathlib import Path

    import dlite
    from oteapi.datacache import DataCache
    from tripper import OWL, RDF, RDFS, Namespace, Triplestore
    from tripper.convert import load_container, save_container

    from oteapi_dlite.strategies.generate import DLiteGenerateStrategy
    from oteapi_dlite.strategies.settings import SettingsStrategy
    from oteapi_dlite.utils import get_meta

    thisdir = Path(__file__).resolve().parent
    outdir = thisdir / ".." / "output"

    EMMO = Namespace(
        iri="https://w3id.org/emmo#",
        label_annotations=True,
        check=True,
    )

    # Create/clear KB
    kb = outdir / "kb.ttl"
    ts = Triplestore(backend="rdflib")
    ts.bind("", "http://myproj.org/kb#")
    ts.add_triples(
        [
            (":Sim", RDF.type, OWL.Class),
            (":Sim", RDFS.subClassOf, EMMO.Computation),
            (":input1", RDF.type, ":Input1"),
            (":input2", RDF.type, ":Input2"),
        ]
    )
    ts.add_restriction(":Sim", EMMO.hasInput, ":Input1", "exactly", 1)
    ts.add_restriction(":Sim", EMMO.hasInput, ":Input2", "exactly", 1)
    ts.add_restriction(":Sim", EMMO.hasOutput, ":Output", "exactly", 1)
    input1 = {
        "dataresource": {
            "type": ":Input1",
            "downloadUrl": "file1.json",
            "mediaType": "application/vnd.dlite-parse",
            "configuration": {
                "metadata": "http://onto-ns.com/meta/ex/0.1/Input1",
                "driver": "json",
            },
        },
    }
    input2 = {
        "dataresource": {
            "type": ":Input2",
            "downloadUrl": "file2.yaml",
            "mediaType": "application/vnd.dlite-parse",
            "configuration": {
                "metadata": "http://onto-ns.com/meta/ex/0.1/Input2",
                "driver": "yaml",
            },
        },
    }
    save_container(ts, input1, ":input1", recognised_keys="basic")
    save_container(ts, input2, ":input2", recognised_keys="basic")
    ts.serialize(kb)
    ts.close()

    kb_kwargs = {"backend": "rdflib", "triplestore_url": str(kb)}
    settings_config = {
        "filterType": "application/vnd.dlite-settings",
        "configuration": {
            "label": "tripper.triplestore",
            "settings": kb_kwargs,
        },
    }
    config = {
        "functionType": "application/vnd.dlite-generate",
        "configuration": {
            "label": "image",
            "driver": "json",
            "location": str(outdir / "image.json"),
            "options": "mode=w",
            "kb_document_class": ":MyData",
            "kb_document_base_iri": "http://ex.com#",
            "kb_document_context": {EMMO.isDescriptionFor: ":MyMaterial"},
            "kb_document_computation": ":Sim",
        },
    }

    coll = dlite.Collection()

    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]], [[3], [4]]]
    coll.add("image", image)

    session = {"collection_id": coll.uuid}
    DataCache().add(coll.asjson(), key=coll.uuid)

    # Execute pipeline...
    strategy = SettingsStrategy(settings_config)
    session.update(strategy.initialize(session))

    strategy = DLiteGenerateStrategy(config)
    session.update(strategy.initialize(session))

    strategy = DLiteGenerateStrategy(config)
    session.update(strategy.get(session))

    strategy = SettingsStrategy(settings_config)
    session.update(strategy.get(session))

    # Check that the data in the newly created generated json file matches our
    # image instance.
    # Fefore loading the generated file, we delete the original image instance
    # to ensure that we are not just fetching it from the dlite cache...
    image_dict = image.asdict()
    del image
    image2 = dlite.Instance.from_location(
        "json", outdir / "image.json", "mode=r"
    )
    assert image2.asdict() == image_dict

    # Check data documentation in KB
    ts = Triplestore(**kb_kwargs)

    # Get IRI of the created data individual
    iri = ts.value(predicate=RDF.type, object=":MyData")
    assert iri.startswith("http://ex.com#mydata-")

    doc = load_container(
        ts, iri, recognised_keys="basic", ignore_unrecognised=True
    )
    assert doc == {
        "dataresource": {
            "type": ":MyData",
            "downloadUrl": str((outdir / "image.json")),
            "mediaType": "application/vnd.dlite-parse",
            "configuration": {
                "driver": "json",
                "options": "mode=w",
                "metadata": "http://onto-ns.com/meta/1.0/Image",
            },
        },
    }

    # Check kb_document_class
    assert ts.has(iri, RDF.type, ":MyData")

    # Check kb_document_context
    assert ts.has(iri, EMMO.isDescriptionFor, ":MyMaterial")

    # Check: kb_document_computation
    sim = ts.value(predicate=RDF.type, object=":Sim")
    assert sim.startswith("http://ex.com#sim-")
    assert ts.has(sim, EMMO.hasInput, ":input1")
    assert ts.has(sim, EMMO.hasInput, ":input2")
    assert ts.has(sim, EMMO.hasOutput, iri)
