"""Test the image formats in the image parse strategy."""

# pylint: disable=too-many-locals
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional

    from oteapi.interfaces import IParseStrategy

    from oteapi_dlite.models import DLiteSessionUpdate


def test_parse_no_options(
    static_files: "Path",
) -> None:
    """Test the dlite-parse strategy."""

    import dlite
    from oteapi.datacache import DataCache

    from oteapi_dlite.strategies.parse import DLiteParseStrategy

    sample_file = static_files / "molecule.json"

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

    # How to reach the instance if we do not have a label?
    # coll2: dlite.Collection = dlite.get_instance(session["collection_id"])
    # inst: dlite.Instance = coll2.get("instance")
    # assert ...


def test_parse_label(
    static_files: "Path",
) -> None:
    """Test the dlite-parse strategy."""

    import dlite
    from oteapi.datacache import DataCache

    from oteapi_dlite.strategies.parse import DLiteParseStrategy

    sample_file = static_files / "molecule.json"

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
