"""Tests for oteapi-dlite.utils"""


# if True:
def test_settings():
    """Test add_settings() and get_settings()."""
    from oteapi_dlite.utils import add_settings, get_settings

    session = {}
    settings1 = {"a": 1, "b": None}
    settings2 = None
    settings3 = [1, settings1]

    add_settings(session, "settings1", settings1)
    add_settings(session, "settings2", settings2)
    add_settings(session, "settings3", settings3)

    assert get_settings(session, "settings1") == settings1
    assert get_settings(session, "settings2") == settings2
    assert get_settings(session, "settings3") == settings3
    assert get_settings(session, "non-existing-settings") is None


# if True:
def test_update_dict():
    """Test update_dict()."""
    import pytest

    from oteapi_dlite.utils import TypeMismatchError, update_dict

    dct = {
        "a": 1,
        "b": {
            "c": [1, 2, 3],
            "d": None,
            "e": {"f": "string_value"},
        },
    }

    d1 = update_dict(dct.copy(), {"a": 2.2})
    assert d1["a"] == 2.2  # Accept conversion between numbers types
    assert d1["b"] == dct["b"]

    d2 = update_dict(dct.copy(), {"b": {"c": [5]}})
    assert d2["a"] == dct["a"]
    assert d2["b"]["c"] == [5]
    assert d2["b"]["d"] == dct["b"]["d"]
    assert d2["b"]["e"] == dct["b"]["e"]

    # Do not accept conversion between other types
    with pytest.raises(TypeMismatchError):
        update_dict(dct.copy(), {"a": "abc..."})
