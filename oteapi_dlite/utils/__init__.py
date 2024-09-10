"""`oteapi_dlite.utils` module.

This module provide some utility functions.
"""

from .nputils import dict2recarray
from .rdf import save, to_triples  # , load
from .utils import (
    add_settings,
    get_collection,
    get_driver,
    get_instance,
    get_meta,
    get_settings,
    update_collection,
)

__all__ = (
    "add_settings",
    "dict2recarray",
    "get_collection",
    "get_driver",
    "get_instance",
    "get_meta",
    "get_settings",
    # "load",
    "save",
    "to_triples",
    "update_collection",
)
