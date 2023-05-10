"""OTEAPI-DLite exceptions."""


class OteapiDliteException(Exception):
    """A catch-em-all generic OTEAPI-DLite exception."""


class CollectionNotFound(OteapiDliteException):
    """A dlite.Collection could not be found."""
