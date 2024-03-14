"""Tests generate strategy."""

from pathlib import Path

import dlite
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

FORCES = Namespace("http://onto-ns.com/meta/0.1/Forces#")
ENERGY = Namespace("http://onto-ns.com/meta/0.1/Energy#")
coll = dlite.Collection()
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
    configuration={"collection_id": coll.uuid},
)

config2 = DLiteGenerateConfig(
    functionType="application/vnd.dlite-generate",
    configuration={
        "datamodel": "http://onto-ns.com/meta/0.1/Result",
        "driver": "json",
        "location": str(outdir / "results.json"),
        "options": "mode=w",
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

mapper = DLiteMappingStrategy(config1)
mapper.initialize()

generator = DLiteGenerateStrategy(config2)
generator.get()
