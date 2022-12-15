"""`oteapi_dlite.utils` module.

This module provide some utility functions.
"""
from .nputils import dict2recarray
from .utils import (
    DLiteGlobalConfiguration,
    get_collection,
    get_driver,
    get_instance,
    get_meta,
    update_collection,
)

__all__ = (
    "DLiteGlobalConfiguration",
    "dict2recarray",
    "get_driver",
    "get_meta",
    "get_instance",
    "get_collection",
    "update_collection",
)
