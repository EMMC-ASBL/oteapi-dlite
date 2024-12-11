"""OTEAPI-DLite exceptions."""

from __future__ import annotations


class OteapiDliteException(Exception):
    """A catch-em-all generic OTEAPI-DLite exception."""


class CollectionNotFound(OteapiDliteException):
    """A dlite.Collection could not be found."""
