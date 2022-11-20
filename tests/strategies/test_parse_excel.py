"""Test parse strategies."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from oteapi.interfaces import IParseStrategy


def test_parse_excel(static_files: "Path") -> None:
    """Test excel parse strategy."""
    import dlite
    import numpy as np
    from oteapi.datacache import DataCache

    from oteapi_dlite.strategies.parse_excel import DLiteExcelStrategy

    sample_file = static_files / "test_parse_excel.xlsx"

    cache_key = DataCache().add(sample_file.read_bytes())
    config = {
        "downloadUrl": sample_file.as_uri(),
        "mediaType": "application/vnd.dlite-xlsx",
        "configuration": {
            "excel_config": {
                "worksheet": "Sheet1",
                "header_row": "1",
                "row_from": "2",
            },
        },
    }

    coll = dlite.Collection()
    session = {
        "collection_id": coll.uuid,
        "key": cache_key,
    }

    parser = DLiteExcelStrategy(config)
    session.update(parser.initialize(session))

    # Note that initialize() and get() are called on different parser
    # instances...
    parser: "IParseStrategy" = DLiteExcelStrategy(config)
    parser.get(session)

    inst = coll.get("excel-data")

    assert np.all(inst.Sample == ["A", "B", "C", "D"])
    assert np.allclose(inst.Temperature, [293.15, 300, 320, 340])
    assert np.all(inst.Pressure == [100000, 200000, 300000, 400000])
