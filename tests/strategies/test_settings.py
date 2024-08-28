"""Test settings strategy."""

if True:
    # def test_settings() -> None:
    """Test the settings strategy."""

    from oteapi_dlite.strategies.settings import SettingsStrategy
    from oteapi_dlite.utils import get_settings

    my_settings = {"key1": "val1", "key2": 3.14, "key3": [1, 2, 3]}
    config = {
        "filterType": "image/vnd.dlite-settings",
        "configuration": {
            "label": "mySettings",
            "settings": my_settings,
        },
    }
    session = {}

    strategy = SettingsStrategy(config)
    strategy.initialize(session)

    strategy = SettingsStrategy(config)
    strategy.get(session)

    assert get_settings(session, "mySettings") == my_settings
    assert get_settings(session, "no-such-settings") is None
