"""Test convert strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_convert(inputdir: Path, outputdir: Path) -> None:
    """
    Test convert strategy
    """
    from otelib import OTEClient
    from yaml import safe_load

    resultfile = outputdir / "result.yaml"

    client = OTEClient("python")

    energy_resource = client.create_dataresource(
        resourceType="resource/url",
        downloadUrl=(inputdir / "energy.yaml").as_uri(),
        mediaType="application/yaml",
    )

    energy_resource_parser = client.create_parser(
        parserType="application/vnd.dlite-parse",
        entity="http://example.org",
        configuration={
            "driver": "yaml",
            "options": "mode=r",
            "label": "energy",
        },
    )

    forces_resource = client.create_dataresource(
        resourceType="resource/url",
        downloadUrl=(inputdir / "forces.yaml").as_uri(),
        mediaType="application/yaml",
    )

    forces_resource_parser = client.create_parser(
        parserType="application/vnd.dlite-parse",
        entity="http://example.org",
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
    pipeline = (
        energy_resource
        >> energy_resource_parser
        >> forces_resource
        >> forces_resource_parser
        >> convert
        >> generate
    )
    pipeline.get()

    # Ensure that the result file is regenerated
    assert resultfile.exists()

    # Check result content
    with resultfile.open(encoding="utf8") as f:
        dct = safe_load(f)
    _, d = dct.popitem()
    assert d["meta"] == "http://onto-ns.com/meta/0.1/Result"
    assert d["dimensions"] == {"natoms": 2, "ncoords": 3}
    assert d["properties"] == {
        "potential_energy": 2.1,
        "forces": [[0.1, 0.0, 0.3], [0.5, 0.0, 0.0]],
    }


def test_convert_with_options(inputdir: Path, outputdir: Path) -> None:
    """
    Test convert strategy
    """
    from otelib import OTEClient

    resultfile = outputdir / "result.yaml"

    client = OTEClient("python")

    energy_resource = client.create_dataresource(
        resourceType="resource/url",
        downloadUrl=(inputdir / "energy.yaml").as_uri(),
        mediaType="application/yaml",
    )

    energy_resource_parser = client.create_parser(
        parserType="application/vnd.dlite-parse",
        entity="http://example.org",
        configuration={
            "driver": "yaml",
            "options": "mode=r",
            "label": "energy",
        },
    )

    forces_resource = client.create_dataresource(
        resourceType="resource/url",
        downloadUrl=(inputdir / "forces.yaml").as_uri(),
        mediaType="application/yaml",
    )

    forces_resource_parser = client.create_parser(
        parserType="application/vnd.dlite-parse",
        entity="http://example.org",
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
            "function_name": "converter_w_options",
            "inputs": [
                {"label": "energy"},
                {"label": "forces"},
            ],
            "outputs": [
                {"label": "result"},
            ],
            "kwargs": {"test_option": "fun"},
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
    pipeline = (
        energy_resource
        >> energy_resource_parser
        >> forces_resource
        >> forces_resource_parser
        >> convert
        >> generate
    )
    pipeline.get()

    # Ensure that the result file is regenerated
    assert resultfile.exists()
