"""Test convert strategy."""
from typing import TYPE_CHECKING

from otelib import OTEClient
from paths import inputdir, outputdir

if TYPE_CHECKING:
    from oteapi.interfaces import IParseStrategy


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

# Remove result file, so that we can check that it is generated
resultfile = outputdir / "result.yaml"
if resultfile.exists():
    resultfile.unlink()

generate = client.create_function(
    functionType="application/vnd.dlite-generate",
    configuration={
        "driver": "yaml",
        "location": str(resultfile),
        "options": "mode=w",
        "label": "result",
    },
)


# Run pipeline
pipeline = energy_resource >> forces_resource >> convert >> generate
pipeline.get()

assert resultfile.exists()
