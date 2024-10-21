"""Utility functions for OTEAPI DLite plugin."""

from __future__ import annotations

import json
from numbers import Number
from pathlib import Path
from typing import TYPE_CHECKING

import dlite
from dlite.mappings import instantiate
from oteapi.datacache import DataCache
from oteapi.models import SessionUpdate

from oteapi_dlite.utils.exceptions import CollectionNotFound

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Optional, Union

    from tripper import Triplestore

    NoneType = type(None)


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
    "minio": "minio",
    "mongodb": "mongodb",
    "postgresql": "postgresql",
}


def get_collection(
    session: Optional[dict[str, Any]] = None,
    collection_id: Optional[str] = None,
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

    if session is None:
        session = {}

    id_ = collection_id or session.get("collection_id")

    # Storing the collection in the datacache is not scalable.
    # Do we really want to do that?
    #
    # Currently we check the datacache first and then ask dlite to look
    # up the collection (which is the proper and scalable solution).
    if id_ is None:
        coll = dlite.Collection()
        cache.add(coll.asjson(), key=coll.uuid)
    elif id_ in cache:
        coll = dlite.Instance.from_json(cache.get(id_), id=id_)
    else:
        try:
            coll = dlite.get_instance(id_)
        except dlite.DLiteError as exc:
            raise CollectionNotFound(
                f"Could not find DLite Collection with id {id_}"
            ) from exc

    if coll.meta.uri != dlite.COLLECTION_ENTITY:
        raise CollectionNotFound(f"instance with id {id_} is not a collection")

    if "collection_id" not in session:
        session["collection_id"] = coll.uuid

    return coll


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


def get_driver(
    mediaType: Optional[str] = None,
    accessService: Optional[str] = None,
) -> str:
    """Return name of DLite driver for the given media type/access service."""
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
    meta: Union[str, dlite.Metadata],
    session: Optional[dict[str, Any]] = None,
    collection: Optional[dlite.Collection] = None,
    routedict: Optional[dict] = None,
    instance_id: Optional[str] = None,
    allow_incomplete: bool = False,
    **kwargs,
) -> dlite.Instance:
    """Instantiates and returns an instance of `meta`.

    Arguments:
        meta: Metadata to instantiate.  Typically its URI.
        session: An OTEAPI session object.
        collection: The collection with instances and mappings.
            The default is to get the collection from `session`.

    Some less used optional arguments:
        routedict: Dict mapping property names to route number to select for
            the given property.  The default is to select the route with
            lowest cost.
        instance_id: URI of instance to create.
        allow_incomplete: Whether to allow not populating all properties
            of the returned instance.
        kwargs: Additional arguments passed to dlite.mappings.instantiate().
    """
    # Import here to avoid a hard dependency on tripper.
    from tripper import Triplestore

    if collection is None:
        if session is None:
            raise TypeError(
                "get_instance() requires that either `session` or "
                "`collection` argument is given."
            )
        collection = get_collection(session)

    if session:
        ts = get_triplestore(session)
    else:
        ts = Triplestore(backend="collection", collection=collection)

    return instantiate(
        meta=meta,
        instances=list(collection.get_instances()),
        triplestore=ts,
        routedict=routedict,
        id=instance_id,
        allow_incomplete=allow_incomplete,
        **kwargs,
    )


def add_settings(
    session: Union[dict[str, Any], None],
    label: str,
    settings: Union[  # noqa: PYI041
        dict, list, str, int, float, bool, NoneType
    ],
) -> SessionUpdate:
    """Store settings to the session.

    Arguments:
        session: An OTEAPI session object.
        label: Label of settings to add.
        settings: A JSON-serialisable Python object with the settings
            to store.

    Returns:
        A SessionUpdate instance with the added settings.
    """
    if session is None:
        session = {}

    # For now we store settings in the session.  This makes "settings"
    # independent of oteapi-dlite.
    d = session.get("settings", {})

    if label in d:
        raise KeyError(f"Setting with this label already exists: '{label}'")
    d[label] = json.dumps(settings)

    # Update the session with new settings
    session["settings"] = d

    return SessionUpdate(settings=d)


def get_settings(session: Union[dict[str, Any], None], label: str) -> Any:
    """Retrieve settings from the session.

    Arguments:
        session: An OTEAPI session object.
        label: Label of settings to retrieve.

    Returns:
        Python object with the settings or None if no settings exists
        with this label.
    """
    if session is None:
        session = {}

    d = session.get("settings", {})
    return json.loads(d[label]) if label in d else None


def get_triplestore(
    session: dict[str, Any],
) -> Triplestore:
    """Return a tripper.Triplestore instance for the current session.

    If a 'tripper.triplestore' setting has been added with the
    SettingsStrategy, it will be used to configure the returned
    triplestore instance.  Otherwise the session collection will be
    used.
    """
    # Import here to avoid a hard dependency on tripper.
    from tripper import Triplestore

    kb_settings = get_settings(session, "tripper.triplestore")
    if kb_settings:
        ts = Triplestore(**kb_settings)
    else:
        coll = get_collection(session)
        ts = Triplestore(backend="collection", collection=coll)
    return ts


class TypeMismatchError(TypeError):
    """Raised by update_dict() if there is a mismatch in value types
    between the `dct` and `update` dictionaries.
    """


class RemoveItem:
    """Singleton class used by update_dict() to indicate items that should
    be removed in the source dictionary."""


def update_dict(dct: dict, update: Optional[dict]) -> dict:
    """Update dictionary `dct` using dictionary `update`.

    This function differ from `dict.update()` in that it updates
    sub-directories recursively, instead of replacing them with the
    content of `update`.

    If `update` has `RemoveItem` as a value, the corresponding item
    in `dct` will be removed.

    Arguments:
        dct: Dict to update.
        update: Dict used to update `conf` with.

    Returns:
        The updated dict `dct`.

    Raises:
        TypeMismatchError: If there is a mismatch in value types
            between the `dct` and `update` dictionaries.  Conversion
            between different number types is accepted.

    """
    if not update:
        return dct

    for k, v in dct.items():
        if k in update:

            if update[k] is RemoveItem:
                del dct[k]
                continue

            if not (
                (isinstance(update[k], Number) and isinstance(v, Number))
                or isinstance(update[k], type(v))
            ):
                raise TypeMismatchError(
                    f"type of `update['{k}']` ({type(update[k])!r}) is not a "
                    f"subclass of the type of `dct['{k}']` ({type(v)!r})"
                )

            if isinstance(v, dict):
                update_dict(v, update[k])
            else:
                dct[k] = update[k]

    # Add new items to `dct`
    for k, v in update.items():
        if k not in dct:
            dct[k] = v

    return dct
