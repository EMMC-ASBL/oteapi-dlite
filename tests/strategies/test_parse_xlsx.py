"""Test parse strategies."""
from pathlib import Path


def test_parse_excel():
    """Test `text/json` parse strategy."""
    import dlite
    import numpy as np
    from oteapi.models import ResourceConfig

    from oteapi_dlite.strategies.parse_xlsx import DLiteXLSXParseStrategy

    thisdir = Path(__file__).absolute().parent

    config = ResourceConfig(
        downloadUrl=f"file://{thisdir}/test_parse_xlsx.xlsx",
        mediaType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        configuration={
            "xlsx_config": {
                "worksheet": "Sheet1",
                "header_row": "1",
                "row_from": "2",
            },
        },
    )

    coll = dlite.Collection()
    session = {"collection_id": coll.uuid}

    parser = DLiteXLSXParseStrategy(config)
    session.update(parser.initialize(session))

    parser = DLiteXLSXParseStrategy(config)
    parser.get(session)

    inst = coll.get("excel-data")

    print(inst.meta)
    print()
    print(inst)
    assert np.all(inst.Sample == ["A", "B", "C", "D"])
    assert np.allclose(inst.Temperature, [293.15, 300, 320, 340])
    assert np.all(inst.Pressure == [100000, 200000, 300000, 400000])
