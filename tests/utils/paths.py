"""Paths used by the tests."""

from pathlib import Path

# Paths
thisdir = Path(__file__).resolve().parent
testdir = thisdir.parent
inputdir = testdir / "input"
outputdir = testdir / "output"
