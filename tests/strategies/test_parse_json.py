"""Test parse_json Strategy"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from oteapi.interfaces import IParseStrategy


def test_parse_json(static_files: "Path") -> None:
    """Test json parse strategy."""
    import dlite

    from oteapi_dlite.strategies.parse_json import (
        DLiteJsonStrategy,
        DLiteJsonStrategyConfig,
    )

    sample_file = static_files / "test_parse_json.json"

    coll = dlite.Collection()
    config = DLiteJsonStrategyConfig.model_validate(
        {
            "entity": "http://onto-ns.com/meta/0.4/HallPetch",
            "parserType": "json/vnd.dlite-json",
            "configuration": {
                "collection_id": coll.uuid,
                "downloadUrl": sample_file.as_uri(),
                "mediaType": "application/json",
                "resourceType": "resource/url",
            },
        }
    )
    parser: "IParseStrategy" = DLiteJsonStrategy(parse_config=config)
    parser.initialize()
    parser.get()

    inst = coll.get("json-data")
    assert inst.theta0 == 50
    assert inst.k == 0.02
    assert inst.d == 0.0005
