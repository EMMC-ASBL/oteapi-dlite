"""Tests storing documentation of instance with the generate strategy."""

# pylint: disable=too-many-locals


# if True:
def test_generate_kb():
    """Test generate with kb documentation enabled."""
    from pathlib import Path

    import dlite
    from oteapi.datacache import DataCache
    from tripper import EMMO, RDF, Triplestore
    from tripper.convert import load_container

    from oteapi_dlite.strategies.generate import DLiteGenerateStrategy
    from oteapi_dlite.strategies.settings import SettingsStrategy
    from oteapi_dlite.utils import get_meta

    thisdir = Path(__file__).resolve().parent
    outdir = thisdir / ".." / "output"

    # Create/clear KB
    kb = outdir / "kb.ttl"
    kb.write_text("")

    iri = "https://example.org/data/mydata"

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
            "kb_document_iri": iri,
            "kb_document_context": {RDF.type: EMMO.DataSet},
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
    doc = load_container(ts, iri, recognised_keys="basic")
    assert doc == {
        "dataresource": {
            "downloadUrl": str((outdir / "image.json")),
            "mediaType": "application/vnd.dlite-parse",
            "configuration": {
                "driver": "json",
                "options": "mode=w",
                "metadata": "http://onto-ns.com/meta/1.0/Image",
            },
        },
    }
    assert ts.has(iri, RDF.type, EMMO.DataSet)
