"""Tests serialise strategy."""

def test_serialise(tmp_dir):
    """Test the serialise filter."""
    import dlite
    from oteapi.models.filterconfig import FilterConfig

    from oteapi_dlite.strategies.serialise import (
        SerialiseStrategy,
        SerialiseFilterConfig,
        SerialiseConfig,
    )
    from oteapi_dlite.utils import get_meta

    config = SerialiseFilterConfig(
        filterType="dlite_serialise",
        configuration={
            "driver": "json",
            "location": str(tmp_dir / "coll.json"),
            "options": "mode=w",
            "labels": ["image"],
        },
    )

    coll = dlite.Collection()
    session = {"collection_id": coll.uuid}

    serialiser = SerialiseStrategy(config)
    session.update(serialiser.initialize(session))

    # Imitate other filters adding stuff to the collection
    coll.add_relation("subject", "predicate", "object")
    Image = get_meta("http://onto-ns.com/meta/1.0/Image")
    image = Image([2, 2, 1])
    image.data = [[[1], [2]],[[3], [4]]]
    coll.add("image", image)

    serialiser = SerialiseStrategy(config)
    session.update(serialiser.get(session))

    assert (tmp_dir / "coll.json").exists()
