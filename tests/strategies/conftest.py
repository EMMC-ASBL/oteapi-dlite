"""Pytest fixtures for the strategies module."""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def testdir() -> "Path":
    """Path to the directory containing this file."""
    from pathlib import Path

    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def entitydir(testdir: "Path") -> "Path":
    """Path to the entities directory."""
    return testdir / "entities"


@pytest.fixture(scope="session")
def inputdir(testdir: "Path") -> "Path":
    """Path to the input directory."""
    return testdir / "input"


@pytest.fixture(scope="session")
def outputdir(testdir: "Path") -> "Path":
    """Path to the output directory."""
    return testdir / "output"


@pytest.fixture(scope="session")
def staticdir(testdir: "Path") -> "Path":
    """Path to the static directory."""
    return testdir / "static"


def pytest_configure(config):
    """Configure pytest."""
    # Add utils to sys path
    import sys

    sys.path.append(str(testdir))


@pytest.fixture(scope="session", autouse=True)
def _update_dlite_storage_path(entitydir: "Path") -> None:
    """Update the DLite storage path to include the entities directory."""
    import dlite

    dlite.storage_path.append(str(entitydir))
