"""Test generate from mappings."""

# if True:
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..conftest import PathsTuple


def test_generate_from_mappings(paths: PathsTuple) -> None:
    """Test generate from mappings."""
    import dlite
    from oteapi.datacache import DataCache
    from oteapi.utils.config_updater import populate_config_from_session
    from tripper import EMMO, MAP

    from oteapi_dlite.strategies.generate import (
        DLiteGenerateConfig,
        DLiteGenerateStrategy,
    )
    from oteapi_dlite.strategies.mapping import (
        DLiteMappingConfig,
        DLiteMappingStrategy,
    )
    from oteapi_dlite.utils import get_meta

    coll = dlite.Collection()

    mapping_config = DLiteMappingConfig(
        mappingType="mappings",
        prefixes={
            "f": "http://onto-ns.com/meta/0.1/Forces#",
            "e": "http://onto-ns.com/meta/0.1/Energy#",
            "r": "http://onto-ns.com/meta/0.1/Result#",
            "map": str(MAP),  # __FIXME__: prefixes should accept a Namespace
            "emmo": str(EMMO),
        },
        triples=[
            ("f:forces", "map:mapsTo", "emmo:Force"),
            ("e:energy", "map:mapsTo", "emmo:PotentialEnergy"),
            ("r:forces", "map:mapsTo", "emmo:Force"),
            ("r:potential_energy", "map:mapsTo", "emmo:PotentialEnergy"),
        ],
        configuration={"collection_id": coll.uuid},
    )

    generate_config = DLiteGenerateConfig(
        functionType="application/vnd.dlite-generate",
        configuration={
            "datamodel": "http://onto-ns.com/meta/0.1/Result",
            "driver": "json",
            "location": str(paths.outputdir / "results.json"),
            "options": "mode=w",
            # Remove collection_id here when EMMC-ASBL/oteapi#545 is fixed
            "collection_id": coll.uuid,
        },
    )

    Energy = get_meta("http://onto-ns.com/meta/0.1/Energy")
    energy = Energy()
    energy.energy = 0.2  # eV

    Forces = get_meta("http://onto-ns.com/meta/0.1/Forces")
    forces = Forces(dimensions={"natoms": 2, "ncoords": 3})
    forces.forces = [[0.1, 0.0, -3.2], [0.0, -2.3, 1.2]]  # eV/Å

    coll.add("energy", energy)
    coll.add("forces", forces)

    # Hmm, the collection should live in a proper shared storage
    cache = DataCache()
    cache.add(coll.asjson(), key=coll.uuid)

    session = DLiteMappingStrategy(mapping_config).initialize()

    populate_config_from_session(session, generate_config)
    DLiteGenerateStrategy(generate_config).get()

    # Check stored results
    result_file = paths.outputdir / "results.json"
    assert result_file.exists()

    r = dlite.Instance.from_location("json", result_file)
    assert r.meta.uri == "http://onto-ns.com/meta/0.1/Result"
    assert r.dimensions == {"natoms": 2, "ncoords": 3}
    assert r.forces.shape == (2, 3)
