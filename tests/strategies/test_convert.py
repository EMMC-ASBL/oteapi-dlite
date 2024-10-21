"""Test convert strategy."""

from __future__ import annotations

from pathlib import Path

from otelib import OTEClient
from paths import inputdir, outputdir
from yaml import safe_load


# if True:
def test_convert():
    """
    Test convert strategy
    """
    resultfile = outputdir / "result.yaml"

    client = OTEClient("python")

    energy_resource = client.create_dataresource(
        downloadUrl=(inputdir / "energy.yaml").as_uri(),
        mediaType="application/vnd.dlite-parse",
        configuration={
            "driver": "yaml",
            "options": "mode=r",
            "label": "energy",
        },
    )

    forces_resource = client.create_dataresource(
        downloadUrl=(inputdir / "forces.yaml").as_uri(),
        mediaType="application/vnd.dlite-parse",
        configuration={
            "driver": "yaml",
            "options": "mode=r",
            "label": "forces",
        },
    )

    convert = client.create_function(
        functionType="application/vnd.dlite-convert",
        configuration={
            "module_name": "test_package.convert_module",
            "function_name": "converter",
            "inputs": [
                {"label": "energy"},
                {"label": "forces"},
            ],
            "outputs": [
                {"label": "result"},
            ],
        },
    )

    generate = client.create_function(
        functionType="application/vnd.dlite-generate",
        configuration={
            "driver": "yaml",
            "location": str(resultfile),
            "options": "mode=w",
            "label": "result",
        },
    )

    # Remove result file, so that we can check that it is generated
    if resultfile.exists():
        resultfile.unlink()

    # Run pipeline
    pipeline = energy_resource >> forces_resource >> convert >> generate
    pipeline.get()

    # Ensure that the result file is regenerated
    assert resultfile.exists()

    # Check result content
    with Path(resultfile).open(encoding="utf8") as f:
        dct = safe_load(f)
    _, d = dct.popitem()
    assert d["meta"] == "http://onto-ns.com/meta/0.1/Result"
    assert d["dimensions"] == {"natoms": 2, "ncoords": 3}
    assert d["properties"] == {
        "potential_energy": 2.1,
        "forces": [[0.1, 0.0, 0.3], [0.5, 0.0, 0.0]],
    }
