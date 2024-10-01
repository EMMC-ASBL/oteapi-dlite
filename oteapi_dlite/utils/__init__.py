"""`oteapi_dlite.utils` module.

This module provide some utility functions.
"""

from .nputils import dict2recarray
from .rdf import load_dataset, save_dataset
from .utils import (
    RemoveItem,
    TypeMismatchError,
    add_settings,
    get_collection,
    get_driver,
    get_instance,
    get_meta,
    get_settings,
    get_triplestore,
    update_collection,
    update_dict,
)

__all__ = (
    "RemoveItem",
    "TypeMismatchError",
    "add_settings",
    "dict2recarray",
    "get_collection",
    "get_driver",
    "get_instance",
    "get_meta",
    "get_settings",
    "get_triplestore",
    "load_dataset",
    "save_dataset",
    "update_collection",
    "update_dict",
)
