"""Test script for the add_instance strategy - tested via otelib."""
import os
from pathlib import Path

import dlite
import numpy as np
from otelib import OTEClient

# Paths
thisdir = Path(__file__).resolve().parent
testdir = thisdir.parent
entitydir = testdir / "entities"
outdir = testdir / "output"

os.makedirs(outdir, exist_ok=True)
dlite.storage_path.append(entitydir)


values = {
    "potential_energy": 3.2e-19,
    "forces": [
        [1.2, 2.3, 3.4],
        [0.2, 3.4, 4.5],
    ],
}

# Create OTE client
client = OTEClient("python")

add_instance = client.create_function(
    functionType="application/vnd.dlite-addinstance",
    configuration={
        "datamodel": "http://onto-ns.com/meta/0.1/Result",
        "property_values": values,
        "label": "result",
    },
)


generate = client.create_function(
    functionType="application/vnd.dlite-generate",
    configuration={
        "driver": "json",
        "location": f"{outdir}/test_add_instance.json",
        "options": "mode=w",
        "label": "result",
    },
)

pipeline = add_instance >> generate
pipeline.get()


# Test that the created content is as expected
inst = dlite.Instance.from_location(
    driver="json", location=f"{outdir}/test_add_instance.json", options="mode=r"
)
assert np.allclose(inst.potential_energy, 3.2e-19)
assert np.allclose(inst.forses, [[1.2, 2.3, 3.4], [0.2, 3.4, 4.5]])
