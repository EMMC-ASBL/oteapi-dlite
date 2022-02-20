"""Pytest fixtures for `strategies/`."""
import pytest


@pytest.fixture(scope="session", autouse=True)
def load_plugins() -> None:
    """Load pip installed plugin strategies."""
    from oteapi.plugins.factories import load_strategies

    load_strategies()
