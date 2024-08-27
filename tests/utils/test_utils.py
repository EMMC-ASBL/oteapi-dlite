"""Tests for oteapi-dlite.utils"""

if True:
    # def test_settings():
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
