"""Tests generate strategy."""

# if True:
from __future__ import annotations


def test_generate_from_mappings():
    """Test generate from mappings."""
    from pathlib import Path

    import dlite
    from oteapi.datacache import DataCache
    from tripper import EMMO, MAP, Namespace

    from oteapi_dlite.strategies.generate import (
        DLiteGenerateConfig,
        DLiteGenerateStrategy,
    )
    from oteapi_dlite.strategies.mapping import (
        DLiteMappingConfig,
        DLiteMappingStrategy,
    )
    from oteapi_dlite.utils import get_meta

    thisdir = Path(__file__).resolve().parent
    entitydir = thisdir / ".." / "entities"
    outdir = thisdir / ".." / "output"

    dlite.storage_path.append(entitydir)

    FORCES = Namespace("http://onto-ns.com/meta/0.1/Forces#")  # noqa: F841
    ENERGY = Namespace("http://onto-ns.com/meta/0.1/Energy#")  # noqa: F841

    config1 = DLiteMappingConfig(
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
    )

    config2 = DLiteGenerateConfig(
        functionType="application/vnd.dlite-generate",
        configuration={
            "datamodel": "http://onto-ns.com/meta/0.1/Result",
            "driver": "json",
            "location": str(outdir / "results.json"),
            "options": "mode=w",
        },
    )

    Energy = get_meta("http://onto-ns.com/meta/0.1/Energy")
    energy = Energy()
    energy.energy = 0.2  # eV

    Forces = get_meta("http://onto-ns.com/meta/0.1/Forces")
    forces = Forces(dimensions={"natoms": 2, "ncoords": 3})
    forces.forces = [[0.1, 0.0, -3.2], [0.0, -2.3, 1.2]]  # eV/Å

    coll = dlite.Collection()
    coll.add("energy", energy)
    coll.add("forces", forces)

    # Hmm, the collection should live in a proper shared storage
    cache = DataCache()
    cache.add(coll.asjson(), key=coll.uuid)

    session = {"collection_id": coll.uuid}

    mapper = DLiteMappingStrategy(config1)
    session.update(mapper.initialize(session))

    generator = DLiteGenerateStrategy(config2)
    session.update(generator.get(session))

    # Check stored results
    result_file = outdir / "results.json"
    assert result_file.exists()

    r = dlite.Instance.from_location("json", result_file)
    assert r.meta.uri == "http://onto-ns.com/meta/0.1/Result"
    assert r.dimensions == {"natoms": 2, "ncoords": 3}
    assert r.forces.shape == (2, 3)
