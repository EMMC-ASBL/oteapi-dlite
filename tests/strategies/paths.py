"""Paths used by the tests."""

import sys
from pathlib import Path

import dlite

# Paths
thisdir = Path(__file__).resolve().parent
testdir = thisdir.parent
entitydir = testdir / "entities"
inputdir = testdir / "input"
outputdir = testdir / "output"
staticdir = testdir / "static"


# Add utils to sys path
sys.path.append(str(testdir))


# Add our storage plugin to the DLite plugin search path
# dlite.python_storage_plugin_path.append(plugindir)
dlite.storage_path.append(entitydir)
