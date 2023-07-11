"""Pytest fixtures for `strategies/`."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def load_strategies() -> None:
    """Load pip installed plugin strategies."""
    from oteapi.plugins import load_strategies

    load_strategies()


@pytest.fixture(scope="session")
def repo_dir() -> "Path":
    """Absolute path to the repository directory."""
    from pathlib import Path

    return Path(__file__).resolve().parent.parent.resolve()


@pytest.fixture(scope="session")
def static_files(repo_dir: "Path") -> "Path":
    """Absolute path to the static directory filled with test files."""
    return repo_dir / "tests" / "static"


@pytest.fixture(scope="session")
def entities_path(repo_dir: "Path") -> "Path":
    """Absolute path to the entities directory filled with test DLite
    entities."""
    return repo_dir / "tests" / "entities"
