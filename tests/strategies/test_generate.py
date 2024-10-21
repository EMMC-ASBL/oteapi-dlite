"""Tests generate strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_generate(outputdir: "Path") -> None:
    """Test generate strategy."""
    import dlite
    from oteapi.datacache import DataCache
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.generate import (
        DLiteGenerateConfig,
        DLiteGenerateStrategy,
    )
    from oteapi_dlite.utils import get_meta

    coll = dlite.Collection()

    config = DLiteGenerateConfig(
        functionType="application/vnd.dlite-generate",
        configuration={
            "label": "image",
            "driver": "json",
            "location": str(outputdir / "image.json"),
            "options": "mode=w",
            "collection_id": coll.uuid,
        },
    )

    # Create an image instance and add it to the collection
    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]], [[3], [4]]]
    coll.add("image", image)

    DataCache().add(coll.asjson(), key=coll.uuid)

    session = DLiteGenerateStrategy(config).initialize()

    populate_config_from_session(session, config)

    DLiteGenerateStrategy(config).get()

    # Check that the data in the newly created generated json file matches our
    # image instance.
    # Fefore loading the generated file, we delete the original image instance
    # to ensure that we are not just fetching it from the dlite cache...
    image_dict = image.asdict()
    del image
    image2 = dlite.Instance.from_location(
        "json", outputdir / "image.json", "mode=r"
    )
    assert image2.asdict() == image_dict


def test_store_collection(outputdir: "Path") -> None:
    """Test to store the entire collection with the generate strategy."""
    import dlite
    from oteapi.datacache import DataCache
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.generate import (
        DLiteGenerateConfig,
        DLiteGenerateStrategy,
    )
    from oteapi_dlite.utils import get_meta

    coll = dlite.Collection("coll_id")

    config = DLiteGenerateConfig(
        functionType="application/vnd.dlite-generate",
        configuration={
            "driver": "json",
            "location": str(outputdir / "coll.json"),
            "options": "mode=w",
            "store_collection": True,
            "collection_id": coll.uuid,
        },
    )

    # Create an image instance and add it to the collection
    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]], [[3], [4]]]
    coll.add("image", image)
    coll.add_relation("image", "rdf:type", "onto:Image")
    coll.add_relation("image", "dcterms:title", "Madonna")

    DataCache().add(coll.asjson(), key=coll.uuid)

    session = DLiteGenerateStrategy(config).initialize()

    populate_config_from_session(session, config)

    DLiteGenerateStrategy(config).get()

    # Check that the data in the newly created generated json file matches our
    # collection.
    # Before loading the generated file, we delete the original collection
    # to ensure that we are not just fetching it from the dlite cache...
    del coll
    with dlite.Storage("json", outputdir / "coll.json", "mode=r") as s:
        # Assume we don't know the collection uuid, but we know that there is only
        # one collection in the json file
        (coll_uuid,) = s.get_uuids("http://onto-ns.com/meta/0.1/Collection")
        coll = s.load(id=coll_uuid)
    assert coll.uri == "coll_id"
    assert coll.nrelations == 5
    assert coll["image"] == image


def test_generate_kb(outputdir: "Path") -> None:
    """Test generate with kb documentation enabled."""
    # pylint: disable=too-many-statements
    import dlite
    from otelib import OTEClient
    from tripper import OWL, RDF, RDFS, Namespace, Triplestore
    from tripper.convert import load_container, save_container

    from oteapi_dlite.utils import get_meta

    EMMO = Namespace(
        iri="https://w3id.org/emmo#",
        label_annotations=True,
        check=True,
    )

    # Prepare the knowledge base
    kb = outputdir / "kb.ttl"
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

    # Prepare data
    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]], [[3], [4]]]
    image.save("yaml", outputdir / "image.yaml", "mode=w")

    # Prepare pipeline
    kb_kwargs = {"backend": "rdflib", "triplestore_url": str(kb)}

    client = OTEClient("python")

    resource = client.create_dataresource(
        resourceType="resource/url",
        downloadUrl=(outputdir / "image.yaml").as_uri(),
        mediaType="application/yaml",
    )
    parse = client.create_parser(
        parserType="application/vnd.dlite-parse",
        entity="http://example.org",
        configuration={
            "driver": "yaml",
            "options": "mode=r",
        },
    )
    generate = client.create_function(
        functionType="application/vnd.dlite-generate",
        configuration={
            "datamodel": Image.uri,
            "driver": "json",
            "location": str(outputdir / "image.json"),
            "options": "mode=w",
            "kb_document_class": ":MyData",
            "kb_document_update": {"dataresource": {"license": "MIT"}},
            "kb_document_base_iri": "http://ex.com#",
            # "kb_document_context": {EMMO.isDescriptionFor: ":MyMaterial"},
            "kb_document_computation": ":Sim",
        },
    )
    settings = client.create_filter(
        filterType="application/vnd.dlite-settings",
        configuration={
            "label": "tripper.triplestore",
            "settings": kb_kwargs,
        },
    )

    # Execute pipeline...
    pipeline = resource >> parse >> generate >> settings
    pipeline.get()

    # Check that the data in the newly created generated json file matches our
    # image instance.
    # Fefore loading the generated file, we delete the original image instance
    # to ensure that we are not just fetching it from the dlite cache...
    image_dict = image.asdict()
    del image
    image2 = dlite.Instance.from_location(
        "json", outputdir / "image.json", "mode=r"
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
            "downloadUrl": str((outputdir / "image.json")),
            "mediaType": "application/yaml",
            "license": "MIT",
            "configuration": {
                "driver": "json",
                "options": "mode=r",
                "datamodel": "http://onto-ns.com/meta/1.0/Image",
            },
        },
        # "parse": {}
        "mapping": {
            "mappingType": "mappings",
            # "prefixes": {},
            # "triples": [],
        },
    }

    # Check kb_document_class
    assert ts.has(iri, RDF.type, ":MyData")

    # # Check kb_document_context
    # assert ts.has(iri, EMMO.isDescriptionFor, ":MyMaterial")

    # Check: kb_document_computation
    sim = ts.value(predicate=RDF.type, object=":Sim")
    assert sim.startswith("http://ex.com#sim-")
    assert ts.has(sim, EMMO.hasInput, ":input1")
    assert ts.has(sim, EMMO.hasInput, ":input2")
    assert ts.has(sim, EMMO.hasOutput, iri)


def test_generate_from_mappings(outputdir: "Path") -> None:
    """Test generate from mappings."""
    import dlite
    from oteapi.datacache import DataCache
    from oteapi.utils.config_updater import populate_config_from_session
    from tripper import EMMO, MAP, Namespace

    from oteapi_dlite.strategies.generate import (
        DLiteGenerateConfig,
        DLiteGenerateStrategy,
    )
    from oteapi_dlite.strategies.mapping import (
        DLiteMappingConfig,
        DLiteMappingStrategy,
    )
    from oteapi_dlite.utils import get_meta

    FORCES = Namespace(  # pylint: disable=unused-variable
        "http://onto-ns.com/meta/0.1/Forces#"
    )
    ENERGY = Namespace(  # pylint: disable=unused-variable
        "http://onto-ns.com/meta/0.1/Energy#"
    )

    coll = dlite.Collection()

    mapping_config = DLiteMappingConfig(
        mappingType="mappings",
        prefixes={
            "f": "http://onto-ns.com/meta/0.1/Forces#",
            "e": "http://onto-ns.com/meta/0.1/Energy#",
            "r": "http://onto-ns.com/meta/0.1/Result#",
            "map": str(MAP),  # __FIXME__: prefixes should accept a Namespace
            "emmo": str(EMMO),
        },
        triples=[
            ("f:forces", "map:mapsTo", "emmo:Force"),
            ("e:energy", "map:mapsTo", "emmo:PotentialEnergy"),
            ("r:forces", "map:mapsTo", "emmo:Force"),
            ("r:potential_energy", "map:mapsTo", "emmo:PotentialEnergy"),
        ],
        configuration={"collection_id": coll.uuid},
    )

    generate_config = DLiteGenerateConfig(
        functionType="application/vnd.dlite-generate",
        configuration={
            "datamodel": "http://onto-ns.com/meta/0.1/Result",
            "driver": "json",
            "location": str(outputdir / "results.json"),
            "options": "mode=w",
            # Remove collection_id here when EMMC-ASBL/oteapi#545 is fixed
            "collection_id": coll.uuid,
        },
    )

    Energy = get_meta("http://onto-ns.com/meta/0.1/Energy")
    energy = Energy()
    energy.energy = 0.2  # eV

    Forces = get_meta("http://onto-ns.com/meta/0.1/Forces")
    forces = Forces(dimensions={"natoms": 2, "ncoords": 3})
    forces.forces = [[0.1, 0.0, -3.2], [0.0, -2.3, 1.2]]  # eV/Å

    coll.add("energy", energy)
    coll.add("forces", forces)

    # Hmm, the collection should live in a proper shared storage
    cache = DataCache()
    cache.add(coll.asjson(), key=coll.uuid)

    session = DLiteMappingStrategy(mapping_config).initialize()

    populate_config_from_session(session, generate_config)
    DLiteGenerateStrategy(generate_config).get()

    # Check stored results
    result_file = outputdir / "results.json"
    assert result_file.exists()

    r = dlite.Instance.from_location("json", result_file)
    assert r.meta.uri == "http://onto-ns.com/meta/0.1/Result"
    assert r.dimensions == {"natoms": 2, "ncoords": 3}
    assert r.forces.shape == (2, 3)
