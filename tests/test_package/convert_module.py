"""Test module for convert strategy."""

from pathlib import Path

import dlite
import numpy as np

from oteapi_dlite.utils.exceptions import OteapiDliteException

thisdir = Path(__file__).resolve().parent
entitydir = thisdir.parent / "entities"

dlite.storage_path.append(entitydir)


def converter(energy, forces):
    """Converter."""
    Result = dlite.get_instance("http://onto-ns.com/meta/0.1/Result")
    result = Result(dimensions=forces.dimensions)
    result.potential_energy = energy.energy
    result.forces = forces.forces
    return result


def converter_w_options(energy, forces, test_option):
    """Converter should fail if options not passed to it."""
    if test_option != "fun":
        raise OteapiDliteException
    Result = dlite.get_instance("http://onto-ns.com/meta/0.1/Result")
    result = Result(dimensions=forces.dimensions)
    result.potential_energy = energy.energy
    result.forces = forces.forces

    return result


# Self-tests
Energy = dlite.get_instance("http://onto-ns.com/meta/0.1/Energy")
Forces = dlite.get_instance("http://onto-ns.com/meta/0.1/Forces")

energy = Energy()
energy.energy = 2.1

forces = Forces(dimensions={"natoms": 2, "ncoords": 3})
forces.forces = [
    (0.1, 0.0, 0.3),
    (0.5, 0.0, 0.0),
]

result = converter(energy, forces)

assert np.allclose(result.potential_energy, energy.energy)
assert np.allclose(result.forces, forces.forces)
