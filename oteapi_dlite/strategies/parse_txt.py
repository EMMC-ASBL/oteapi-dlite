"""Strategy that parses resource id and return all associated download links."""
from typing import TYPE_CHECKING, Optional

import requests  # type: ignore
from pydantic import Field
from pydantic.dataclasses import dataclass

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict

import dlite
from oteapi.models import (
    AttrDict,
    DataCacheConfig,
    ResourceConfig,
    SessionUpdate,
)
from pydantic import Field, HttpUrl

from oteapi_dlite.utils import get_collection, update_collection


class TXTConfig(AttrDict):
    """TXT parse-specific Configuration Data Model."""

    datacache_config: Optional[DataCacheConfig] = Field(
        None,
        description=(
            "Configurations for the data cache for storing the downloaded file "
            "content."
        ),
    )
    id: Optional[str] = Field(None, description="Optional id on new instance.")
    metadata: Optional[HttpUrl] = Field(
        None,
        description=(
            "URI of DLite metadata to return.  If not provided, the metadata "
            "will be inferred from the excel file."
        ),
    )

    label: Optional[str] = Field(
        "txt-data",
        description="Optional label for new instance in collection.",
    )

    splitBy: str = Field(
        None,
        description="identifier to split",
    )
    storage_path: Optional[str] = Field(
        None,
        description="Path to metadata storage",
    )


class TXTParseConfig(ResourceConfig):
    """File download strategy filter config."""

    mediaType: str = Field(
        "application/parse-txt",
        const=True,
        description=ResourceConfig.__fields__[
            "mediaType"
        ].field_info.description,
    )

    datacache_config: Optional[DataCacheConfig] = Field(
        None,
        description=(
            "Configurations for the data cache for storing the downloaded file "
            "content."
        ),
    )

    configuration: TXTConfig = Field(
        TXTConfig(), description="TXT parse strategy-specific configuration."
    )


class SessionUpdateTXTParse(SessionUpdate):
    """Class for returning values from TXT Parse."""

    image_metadata: dict = Field(..., description="Image Metadata.")


@dataclass
class TXTDataParseStrategy:
    """Parse strategy for TXT.

    **Registers strategies**:

    - `("mediaType", "application/parse-txt")`

    """

    parse_config: TXTParseConfig

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> SessionUpdate:
        """Initialize."""
        return SessionUpdate()

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> SessionUpdateTXTParse:
        """Download TXT file and return a list of dowload urls for later analysis."""
        coll = get_collection(session)
        config = self.parse_config

        req = requests.get(
            config.downloadUrl,
            allow_redirects=True,
            timeout=(3, 27),  # timeout: (connect, read) in seconds
        )
        image_metadata = parse_metadata(req, config.configuration.splitBy)
        print(image_metadata)
        configuration = config.configuration
        if configuration.metadata:
            if configuration.storage_path is not None:
                for storage_path in configuration.storage_path.split("|"):
                    dlite.storage_path.append(storage_path)
            meta = dlite.get_instance(configuration.metadata)

        inst = meta(dims=[len(image_metadata)], id=configuration.id)
        for name in image_metadata:
            inst[name] = image_metadata[name]
        # # Insert inst into collection
        print("-------------instance------")
        print(inst)
        coll.add(configuration.label, inst)
        update_collection(coll)
        print("-------------collection------")
        print(coll)
        return SessionUpdateTXTParse(image_metadata=image_metadata)


def parse_metadata(response, splitby):
    metadata = {}

    # Decode the content to text and split into lines
    lines = response.content.decode().splitlines()

    for line in lines:
        # Ignore lines that do not contain keyword-value pairs
        if "=" not in line:
            continue

        # Split the line into keyword and value
        keyword, value = line.strip().split(splitby, 1)

        # Ignore empty values
        if not value:
            continue

        # Add the keyword-value pair to the dictionary
        metadata[keyword] = value

    return metadata
