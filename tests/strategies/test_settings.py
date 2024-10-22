"""Test settings strategy."""

from __future__ import annotations


def test_settings() -> None:
    """Test the settings strategy."""
    from oteapi.utils.config_updater import populate_config_from_session

    from oteapi_dlite.strategies.settings import (
        SettingsFilterConfig,
        SettingsStrategy,
    )

    my_settings = {"key1": "val1", "key2": 3.14, "key3": [1, 2, 3]}
    config = {
        "filterType": "image/vnd.dlite-settings",
        "configuration": {
            "label": "mySettings",
            "settings": my_settings,
        },
    }

    # Mock run a pipeline that consists of just a settings strategy
    session = SettingsStrategy(filter_config=config).initialize()

    # Parse config into a pydantic model to use with the
    # populate_config_from_session function
    config = SettingsFilterConfig(**config)
    populate_config_from_session(session=session, config=config)

    session_update = SettingsStrategy(filter_config=config).get()
    assert not session_update

    assert session["dlite_settings"]["mySettings"] == my_settings
    assert session["dlite_settings"].get("no-such-settings") is None
