"""Test convert strategy with options."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..conftest import PathsTuple


def test_convert_with_options(paths: PathsTuple) -> None:
    """
    Test convert strategy
    """
    from otelib import OTEClient

    resultfile = paths.outputdir / "result.yaml"

    client = OTEClient("python")

    energy_resource = client.create_dataresource(
        resourceType="resource/url",
        downloadUrl=(paths.inputdir / "energy.yaml").as_uri(),
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
        downloadUrl=(paths.inputdir / "forces.yaml").as_uri(),
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
            "module_name": "test_package.test_convert_module",
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
