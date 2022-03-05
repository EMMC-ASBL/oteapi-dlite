"""Test parse strategies."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_excel(static_files: "Path") -> None:
    """Test excel parse strategy."""
    import dlite
    import numpy as np
    from oteapi.models import ResourceConfig

    from oteapi_dlite.strategies.parse_excel import DLiteExcelStrategy

    sample_file = static_files / "test_parse_excel.xlsx"

    config = ResourceConfig(
        downloadUrl=sample_file.as_uri(),
        mediaType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        configuration={
            "excel_config": {
                "worksheet": "Sheet1",
                "header_row": "1",
                "row_from": "2",
            },
        },
    )
    print()
    print("config")
    print(config)

    coll = dlite.Collection()
    session = {"collection_id": coll.uuid}

    parser = DLiteExcelStrategy(config)
    session.update(parser.initialize(session))

    # Note that initialize() and get() are called on different parser instances...
    parser = DLiteExcelStrategy(config)
    parser.get(session)

    inst = coll.get("excel-data")

    assert np.all(inst.Sample == ["A", "B", "C", "D"])
    assert np.allclose(inst.Temperature, [293.15, 300, 320, 340])
    assert np.all(inst.Pressure == [100000, 200000, 300000, 400000])
