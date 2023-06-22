"""Tests oteapi-dlite.utils.get_instance()."""
# pylint: disable=too-many-locals
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_instantiate_calcresults(entities_path: "Path") -> None:
    """Test utils.get_instance().

    Instantiate a CalcResult - typically done in a function strategy.

    Notes:
    * The only input we need is the collection and the matadata we
      want to instantiate.  All other information is kept in the collection.
    * Unit conversion is also done transparently.
    * The only thing we are not showing in this test script is how to
      handle mapping functions.

    Parameters:
        entities_path: Path to the `tests/entities/` folder.

    """
    import dlite
    import numpy as np
    from tripper import EMMO, MAP, Triplestore

    from oteapi_dlite.utils import get_instance

    # Setup
    dlite.storage_path.append(str(entities_path / "*.json"))

    # Create collection - called the first time get_collection() is called
    # in a strategy
    coll = dlite.Collection()

    # Populate collection with data - typically done in parse strategies
    Energy = dlite.get_instance("http://onto-ns.com/meta/0.1/Energy")
    Forces = dlite.get_instance("http://onto-ns.com/meta/0.1/Forces")
    energy_inst = Energy()
    energy_inst.energy = 2.1  # eV
    forces_inst = Forces(dimensions={"natoms": 2, "ncoords": 3})
    forces_inst.forces = [(0.0, 0.0, 2.1), (0.0, 0.0, -2.1)]  # eV/Å
    coll.add("energy", energy_inst)
    coll.add("forces", forces_inst)

    # Add mappings1 - typically done in first mapping strategies
    ts = Triplestore(backend="collection", collection=coll)
    FORCES = ts.bind("forces", "http://onto-ns.com/meta/0.1/Forces#")
    ENERGY = ts.bind("energy", "http://onto-ns.com/meta/0.1/Energy#")
    mappings1 = [
        (FORCES.forces, MAP.mapsTo, EMMO.Force),
        (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy),
    ]
    ts.add_triples(mappings1)

    # Add mappings2 - typically done in second mapping strategies
    ts2 = Triplestore(backend="collection", collection=coll)
    CALC = ts2.bind("calc", "http://onto-ns.com/meta/0.1/Result#")
    mappings2 = [
        (CALC.forces, MAP.mapsTo, EMMO.Force),
        (CALC.potential_energy, MAP.mapsTo, EMMO.PotentialEnergy),
    ]
    ts2.add_triples(mappings2)

    inst = get_instance(
        meta="http://onto-ns.com/meta/0.1/Result",
        collection=coll,
    )

    assert inst.dimensions["natoms"] == 2
    assert inst.dimensions["ncoords"] == 3
    assert np.allclose(inst.potential_energy, 3.36457e-19)  # Joule
    assert np.allclose(
        inst.forces,
        [
            (0, 0, 3.36457e-09),  # Newton
            (0, 0, 3.36457e-09),  # Newton
        ],
    )
