"""Test parse strategies."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from oteapi.interfaces import IParseStrategy


def test_parse_excel(static_files: "Path") -> None:
    """Test excel parse strategy."""
    import dlite

    from oteapi_dlite.strategies.parse_json import DLiteJsonStrategy

    sample_file = static_files / "test_parse_json.json"

    coll = dlite.Collection()
    config = (
        {
            "downloadUrl": sample_file.as_uri(),
            "mediaType": "json/vnd.dlite-json",
            "configuration": {
                "collection_id": coll.uuid,
            },
        },
    )

    parser = DLiteJsonStrategy(config)
    parser.initialize()

    # Note that initialize() and get() are called on different parser
    # instances...
    parser: "IParseStrategy" = DLiteJsonStrategy(config)
    parser.get()

    inst = coll.get("json-data")
    print(inst)
    # assert np.all(inst.Sample == ["A", "B", "C", "D"])
    # assert np.allclose(inst.Temperature, [293.15, 300, 320, 340])
    # assert np.all(inst.Pressure == [100000, 200000, 300000, 400000])
