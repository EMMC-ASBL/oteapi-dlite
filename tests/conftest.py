"""Pytest fixtures for `strategies/`."""
import pytest


@pytest.fixture(scope="session", autouse=True)
def load_strategies() -> None:
    """Load strategies."""
    from oteapi.plugins import load_strategies

    load_strategies()
