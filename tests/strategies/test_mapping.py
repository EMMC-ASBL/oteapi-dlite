"""Tests mapping strategy."""

from __future__ import annotations


def test_mapping_without_prefixes() -> None:
    """Test without prefixes."""
    from tripper import EMMO, MAP, Namespace

    from oteapi_dlite.strategies.mapping import (
        DLiteMappingConfig,
        DLiteMappingStrategy,
    )
    from oteapi_dlite.utils import get_collection

    FORCES = Namespace("http://onto-ns.com/meta/0.1/Forces#")
    ENERGY = Namespace("http://onto-ns.com/meta/0.1/Energy#")

    config = DLiteMappingConfig(
        mappingType="mappings",
        triples=[
            (FORCES.forces, MAP.mapsTo, EMMO.Force),
            (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy),
        ],
    )

    session = {}

    strategy = DLiteMappingStrategy(config)
    session.update(strategy.initialize(session))

    strategy = DLiteMappingStrategy(config)
    session.update(strategy.get(session))

    collection = get_collection(session)
    relations = set(collection.get_relations())
    assert (FORCES.forces, MAP.mapsTo, EMMO.Force) in relations
    assert (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy) in relations


def test_mapping_with_prefixes() -> None:
    """Test with prefixes."""
    from tripper import EMMO, MAP, Namespace

    from oteapi_dlite.strategies.mapping import (
        DLiteMappingConfig,
        DLiteMappingStrategy,
    )
    from oteapi_dlite.utils import get_collection

    FORCES = Namespace("http://onto-ns.com/meta/0.1/Forces#")
    ENERGY = Namespace("http://onto-ns.com/meta/0.1/Energy#")

    config = DLiteMappingConfig(
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

    mapper = DLiteMappingStrategy(config)
    session = mapper.initialize()
    session.update(mapper.get(session))

    coll = get_collection(session)

    relations = set(coll.get_relations())
    assert len(list(coll.get_relations())) == len(relations)
    assert (FORCES.forces, MAP.mapsTo, EMMO.Force) in relations
    assert (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy) in relations
