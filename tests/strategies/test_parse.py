"""Test the image formats in the image parse strategy."""

# pylint: disable=too-many-locals
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional

    from oteapi.interfaces import IParseStrategy

    from oteapi_dlite.models import DLiteSessionUpdate


# if True:
def test_parse_no_options() -> None:
    """Test the dlite-parse strategy."""

    import dlite
    from oteapi.datacache import DataCache
    from paths import staticdir

    from oteapi_dlite.strategies.parse import DLiteParseStrategy

    sample_file = staticdir / "molecule.json"

    cache = DataCache()

    orig_key = cache.add(sample_file.read_bytes())
    config = {
        "downloadUrl": sample_file.as_uri(),
        "mediaType": "image/vnd.dlite-parse",
        "configuration": {
            "driver": "json",
        },
    }
    coll = dlite.Collection()
    session = {
        "collection_id": coll.uuid,
        "key": orig_key,
    }
    cache.add(coll.asjson(), key=coll.uuid)
    parser: "IParseStrategy" = DLiteParseStrategy(config)
    output: "DLiteSessionUpdate" = parser.get(session)
    assert "collection_id" in output
    assert output.collection_id == coll.uuid

    # Get all instances of given metaid (there should only be one instance)
    metaid = "http://onto-ns.com/meta/0.1/Molecule"
    instances = list(coll.get_instances(metaid=metaid))
    assert len(instances) == 1
    (inst,) = instances
    assert inst.meta.uri == metaid


# if True:
def test_parse_label() -> None:
    """Test the dlite-parse strategy."""

    import dlite
    from oteapi.datacache import DataCache
    from paths import staticdir

    from oteapi_dlite.strategies.parse import DLiteParseStrategy

    sample_file = staticdir / "molecule.json"

    cache = DataCache()

    orig_key = cache.add(sample_file.read_bytes())
    config = {
        "downloadUrl": sample_file.as_uri(),
        "mediaType": "image/vnd.dlite-parse",
        "configuration": {
            "driver": "json",
            "label": "instance",
        },
    }
    coll = dlite.Collection()
    session = {
        "collection_id": coll.uuid,
        "key": orig_key,
    }
    cache.add(coll.asjson(), key=coll.uuid)
    parser: "IParseStrategy" = DLiteParseStrategy(config)
    output: "DLiteSessionUpdate" = parser.get(session)
    assert "collection_id" in output
    assert output.collection_id == coll.uuid

    coll2: dlite.Collection = dlite.get_instance(session["collection_id"])
    inst: dlite.Instance = coll2.get("instance")
    assert inst.properties.keys() == {
        "name",
        "positions",
        "symbols",
        "masses",
        "groundstate_energy",
    }
    assert inst.properties["name"] == "H2"
