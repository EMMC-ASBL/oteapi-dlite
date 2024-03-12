"""Test convert strategy."""

from otelib import OTEClient
from paths import inputdir, outputdir

resultfile = outputdir / "result.yaml"

client = OTEClient("python")

energy_parser = client.create_parser(
    entity="http://onto-ns.com/meta/0.1/Energy",
    parserType="application/vnd.dlite-parse",
    configuration={
        "driver": "yaml",
        "options": "mode=r",
        "label": "energy",
        "downloadUrl": (inputdir / "energy.yaml").as_uri(),
        "mediaType": "application/json",
    },
)

forces_parser = client.create_parser(
    entity="http://onto-ns.com/meta/0.1/Forces",
    parserType="application/vnd.dlite-parse",
    configuration={
        "driver": "yaml",
        "options": "mode=r",
        "label": "forces",
        "downloadUrl": (inputdir / "forces.yaml").as_uri(),
        "mediaType": "application/json",
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
pipeline = energy_parser >> forces_parser >> convert >> generate
pipeline.get()

# Ensure that the result file is regenerated
assert resultfile.exists()
