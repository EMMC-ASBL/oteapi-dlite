"""Utility functions for OTEAPI DLite plugin."""
# pylint: disable=invalid-name
from pathlib import Path
from typing import TYPE_CHECKING

import dlite
from dlite.mappings import instantiate
from oteapi.datacache import DataCache
from tripper import Triplestore

from oteapi_dlite.utils.exceptions import CollectionNotFound

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Union


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


def get_collection(
    session: "Optional[Dict[str, Any]]" = None,
    collection_id: "Optional[str]" = None,
) -> dlite.Collection:
    """Retrieve a DLite Collection.

    Looks for a Collection UUID in the session.
    If none exists, a new, empty Collection is created and stored in the
    session.

    If `collection_id` is provided, that id is used. If there already is a
    `collection_id` in the session, that is left untouched. Otherwise
    `collection_id` is added to the session.

    Parameters:
        session: An OTEAPI session object.
        collection_id: A specific collection ID to retrieve.

    Return:
        A DLite Collection to be used throughout the OTEAPI session.

    """
    cache = DataCache()

    session = session or {}
    id_ = collection_id or session.get("collection_id")

    if id_ is None:
        collection = dlite.Collection()
        cache.add(collection.asjson(), key=collection.uuid)
    elif id_ not in cache:
        raise CollectionNotFound(
            "Could not find DLite Collection with "
            f"uuid='{session['collection_id']}'"
        )
    else:
        collection = dlite.Collection.from_json(cache.get(id_), id=id_)

    if "collection_id" not in session:
        session["collection_id"] = collection.uuid

    return collection


def update_collection(collection: dlite.Collection) -> None:
    """Update collection in DataCache.

    Parameters:
        collection: The DLite Collection to be updated.

    """
    cache = DataCache()
    cache.add(value=collection.asjson(), key=collection.uuid)


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


def get_instance(
    meta: "Union[str, dlite.Metadata]",
    collection: dlite.Collection,
    routedict: "Optional[dict]" = None,
    instance_id: "Optional[str]" = None,
    allow_incomplete: bool = False,
    **kwargs,
) -> dlite.Instance:
    """Instantiates and returns an instance of `meta`.

    Arguments:
        meta: Metadata to instantiate.  Typically its URI.
        collection: The collection with instances and mappings.

    Some less used optional arguments:
        routedict: Dict mapping property names to route number to select for
            the given property.  The default is to select the route with
            lowest cost.
        instance_id: URI of instance to create.
        allow_incomplete: Whether to allow not populating all properties
            of the returned instance.
        kwargs: Additional arguments passed to dlite.mappings.instantiate().
    """
    ts = Triplestore(backend="collection", collection=collection)
    inst = instantiate(
        meta=meta,
        instances=list(collection.get_instances()),
        triplestore=ts,
        routedict=routedict,
        id=instance_id,
        allow_incomplete=allow_incomplete,
        **kwargs,
    )
    return inst
