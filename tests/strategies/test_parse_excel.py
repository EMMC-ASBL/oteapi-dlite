"""Test parse strategies."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_excel(static_files: Path) -> None:
    """Test excel parse strategy."""
    import dlite
    import numpy as np
    from oteapi.datacache import DataCache
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.parse_excel import DLiteExcelStrategy

    sample_file = static_files / "test_parse_excel.xlsx"

    cache = DataCache()

    cache_key = cache.add(sample_file.read_bytes())
    config = {
        "parserType": "application/vnd.dlite-xlsx",
        "configuration": {
            "excel_config": {
                "worksheet": "Sheet1",
                "header_row": "1",
                "row_from": "2",
            },
            "downloadUrl": sample_file.as_uri(),
            "mediaType": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        },
    }

    coll = dlite.Collection()
    session = {
        "collection_id": coll.uuid,
        "key": cache_key,
    }

    # Mock updating the config with session content
    # This is automatically done as part of a pipeline
    config["configuration"].update(session)

    cache.add(coll.asjson(), key=coll.uuid)

    parser = DLiteExcelStrategy(config)
    parsed_config = parser.parse_config
    session = DLiteExcelStrategy(config).initialize()

    populate_config_from_session(session, parsed_config)

    # Note that initialize() and get() are called on different parser
    # instances...
    DLiteExcelStrategy(parsed_config).get()

    inst = coll.get("excel-data")

    assert np.all(inst.Sample == ["A", "B", "C", "D"])
    assert np.allclose(inst.Temperature, [293.15, 300, 320, 340])
    assert np.all(inst.Pressure == [100000, 200000, 300000, 400000])
