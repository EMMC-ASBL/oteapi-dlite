"""Utility functions for OTEAPI DLite plugin."""
# pylint: disable=invalid-name
import weakref
from pathlib import Path

import dlite

# Set up paths
entities_dir = Path(__file__).parent.parent.resolve() / "entities"
dlite.storage_path.append(f"{entities_dir}/*.json")


# Map mediaType to DLite driver
MEDIATYPES = {
    "application/json": "json",
    "application/yaml": "yaml",
    "application/x-hdf5": "hdf5",
    "application/octet-stream": "blob",
    "application/bson": "bson",
    "application/x-sqlite": "sqlite",
    "application/n-triples": "rdf",
    "text/turtle": "rdf",
    "text/csv": "csv",
    # DLite-specific mediatypes - to be removed
    "application/vnd.dlite-json": "json",
    "application/vnd.dlite-yaml": "yaml",
}

# Map accessService to DLite driver
ACCESSSERVICES = {
    "mongodb": "mongodb",
    "postgresql": "postgresql",
}


def init_session(session):
    """Initialise session if it is not already initialised."""
    if session is None:
        raise ValueError("Missing session")

    if "collection_id" not in session:
        coll = dlite.Collection()
        session["collection_id"] = coll.uuid

        # Make sure that collection stays alive when leaving this function
        coll._incref()  # pylint: disable=protected-access

        # Call _decref() on the collection when `session` is garbage collected
        weakref.finalize(
            session, coll._decref  # pylint: disable=protected-access
        )


def get_meta(uri: str) -> dlite.Instance:
    """Returns metadata corresponding to given uri.

    This function may in the future be connected to a database.
    """
    meta = dlite.get_instance(uri)
    if not meta.is_meta:
        raise ValueError("uri {uri} does not correspond to metadata")
    return meta


def get_driver(mediaType=None, accessService=None, options=None) -> str:
    """Return name of DLite driver for the given media type/access service."""
    # pylint: disable=unused-argument
    if mediaType:
        if mediaType not in MEDIATYPES:
            raise ValueError("unknown DLite mediaType: {mediaType}")
        return MEDIATYPES[mediaType]

    if accessService:
        if accessService not in ACCESSSERVICES:
            raise ValueError("unknown DLite accessService: {accessService}")
        return ACCESSSERVICES[accessService]

    raise ValueError("either `mediaType` or `accessService` must be provided")
