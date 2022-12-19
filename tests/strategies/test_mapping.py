"""Tests mapping strategy."""
import dlite
from tripper import EMMO, MAP, Namespace

from oteapi_dlite.strategies.mapping import (
    DLiteMappingConfig,
    DLiteMappingStrategy,
)

FORCES = Namespace("http://onto-ns.com/meta/0.1/Forces#")
ENERGY = Namespace("http://onto-ns.com/meta/0.1/Energy#")

# Test without prefixes
config = DLiteMappingConfig(
    mappingType="mappings",
    triples=[
        (FORCES.forces, MAP.mapsTo, EMMO.Force),
        (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy),
    ],
)
coll = dlite.Collection()
session = {"collection_id": coll.uuid}

mapper = DLiteMappingStrategy(config)
session.update(mapper.initialize(session))
session.update(mapper.get(session))

relations = set(coll.get_relations())
assert (FORCES.forces, MAP.mapsTo, EMMO.Force) in relations
assert (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy) in relations


# Test with prefixes
config2 = DLiteMappingConfig(
    mappingType="mappings",
    prefixes={
        "f": "http://onto-ns.com/meta/0.1/Forces#",
        "e": "http://onto-ns.com/meta/0.1/Energy#",
        "map": str(MAP),  # __FIXME__: prefixes should accept a Namespace
        "emmo": str(EMMO),
    },
    triples=[
        ("f:forces", "map:mapsTo", "emmo:Force"),
        ("e:energy", "map:mapsTo", "emmo:PotentialEnergy"),
    ],
)
coll2 = dlite.Collection()
session2 = {"collection_id": coll2.uuid}

mapper2 = DLiteMappingStrategy(config2)
session2.update(mapper2.initialize(session2))
session2.update(mapper2.get(session2))

relations2 = set(coll2.get_relations())
assert len(list(coll2.get_relations())) == len(relations2)
assert (FORCES.forces, MAP.mapsTo, EMMO.Force) in relations2
assert (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy) in relations2
