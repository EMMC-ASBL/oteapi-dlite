"""Utility functions for OTEAPI DLite plugin."""
from pathlib import Path

import dlite

# Set up paths
entities_dir = Path(__file__).parent.parent.resolve() / "entities"
dlite.storage_path.append(f"{entities_dir}/*.json")


def get_meta(uri: str) -> dlite.Instance:
    """Returns metadata corresponding to given uri.

    This function may in the future be connected to a database.
    """
    meta = dlite.get_instance(uri)
    if not meta.is_meta:
        raise ValueError("uri {uri} does not correspond to metadata")
    return meta
