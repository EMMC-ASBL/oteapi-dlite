"""Test parse strategies."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from oteapi.interfaces import IParseStrategy


def test_parse_excel(static_files: "Path") -> None:
    """Test excel parse strategy."""
    import dlite
    import numpy as np

    from oteapi_dlite.strategies.parse_excel import DLiteExcelStrategy

    sample_file = static_files / "test_parse_excel.xlsx"

    coll = dlite.Collection()
    config = {
        "entity": "http://onto-ns.com/meta/0.4/Dummy_entity",
        "parserType": "application/vnd.dlite-xlsx",
        "configuration": {
            "excel_config": {
                "worksheet": "Sheet1",
                "header_row": 1,
                "row_from": 2,
            },
            "collection_id": coll.uuid,
            "downloadUrl": sample_file.as_uri(),
            "mediaType": "application/vnd.dlite-xlsx",
            "resourceType": "resource/url",
        },
    }

    parser: "IParseStrategy" = DLiteExcelStrategy(parse_config=config)
    parser.initialize()
    parser.get()

    inst = coll.get("excel-data")

    assert np.all(inst.Sample == ["A", "B", "C", "D"])
    assert np.allclose(inst.Temperature, [293.15, 300, 320, 340])
    assert np.all(inst.Pressure == [100000, 200000, 300000, 400000])
