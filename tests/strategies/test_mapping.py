"""Tests mapping strategy."""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "use_prefixes", (True, False), ids=["with_prefixes", "without_prefixes"]
)
def test_mapping_with_prefixes(use_prefixes: bool) -> None:
    """Test with prefixes."""
    from oteapi.utils.config_updater import populate_config_from_session
    from tripper import EMMO, MAP, Namespace

    from oteapi_dlite.strategies.mapping import (
        DLiteMappingConfig,
        DLiteMappingStrategy,
    )
    from oteapi_dlite.utils import get_collection

    FORCES = Namespace("http://onto-ns.com/meta/0.1/Forces#")
    ENERGY = Namespace("http://onto-ns.com/meta/0.1/Energy#")

    if use_prefixes:
        config_content = {
            "prefixes": {
                "f": "http://onto-ns.com/meta/0.1/Forces#",
                "e": "http://onto-ns.com/meta/0.1/Energy#",
                "map": str(
                    MAP
                ),  # __FIXME__: prefixes should accept a Namespace
                "emmo": str(EMMO),
            },
            "triples": [
                ("f:forces", "map:mapsTo", "emmo:Force"),
                ("e:energy", "map:mapsTo", "emmo:PotentialEnergy"),
            ],
        }
    else:
        config_content = {
            "triples": [
                (FORCES.forces, MAP.mapsTo, EMMO.Force),
                (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy),
            ]
        }

    config = DLiteMappingConfig(mappingType="mappings", **config_content)

    session = DLiteMappingStrategy(config).initialize()

    # Remove the line immediately below once EMMC-ASBL/oteapi#545 is fixed
    config.configuration.collection_id = session.collection_id
    populate_config_from_session(session, config)

    DLiteMappingStrategy(config).get()

    coll = get_collection(session.collection_id)

    relations = set(coll.get_relations())
    assert len(list(coll.get_relations())) == len(relations)
    assert (FORCES.forces, MAP.mapsTo, EMMO.Force) in relations
    assert (ENERGY.energy, MAP.mapsTo, EMMO.PotentialEnergy) in relations
