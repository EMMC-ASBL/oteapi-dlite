"""Pytest fixtures for `strategies/`."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import pytest

if TYPE_CHECKING:
    from pathlib import Path


class PathsTuple(NamedTuple):
    """Tuple of paths."""

    testdir: Path
    entitydir: Path
    inputdir: Path
    outputdir: Path
    staticdir: Path


@pytest.fixture(scope="session")
def paths() -> PathsTuple:
    """Paths tuple."""
    from pathlib import Path

    testdir = Path(__file__).resolve().parent

    return PathsTuple(
        testdir=testdir,
        entitydir=testdir / "entities",
        inputdir=testdir / "input",
        outputdir=testdir / "output",
        staticdir=testdir / "static",
    )


@pytest.fixture(scope="session", autouse=True)
def _update_path_and_dlite_storage_path(paths: PathsTuple) -> None:
    """Update the PATH variable and DLite storage path to include the test
    directory and entities directory, respectively."""
    import sys

    import dlite

    sys.path.append(str(paths.testdir))
    dlite.storage_path.append(str(paths.entitydir))


@pytest.fixture(scope="session", autouse=True)
def _load_strategies() -> None:
    """Load pip installed plugin strategies."""
    from oteapi.plugins import load_strategies

    load_strategies()
