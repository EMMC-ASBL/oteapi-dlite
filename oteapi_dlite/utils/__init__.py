"""`oteapi_dlite.utils` module.

This module provide some utility functions.
"""

from __future__ import annotations

from .nputils import dict2recarray
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
    "get_meta",
    "get_instance",
    "get_settings",
    "get_triplestore",
    "update_collection",
    "update_dict",
)
