"""Strategy for JSON parsing."""

import sys
from typing import Annotated, Optional

import dlite
from oteapi.models import AttrDict, HostlessAnyUrl, ParserConfig, ResourceConfig
from oteapi.plugins import create_strategy
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection
from oteapi_dlite.utils.utils import get_meta

if sys.version_info >= (3, 10):
    from typing import Literal
else:
    from typing_extensions import Literal


class DLiteJsonParseConfig(AttrDict):
    """Configuration for DLite Excel parser."""

    id: Annotated[
        Optional[str], Field(description="Optional id on new instance.")
    ] = None

    label: Annotated[
        Optional[str],
        Field(
            description="Optional label for new instance in collection.",
        ),
    ] = "json-data"

    resourceType: Optional[Literal["resource/url"]] = Field(
        "resource/url",
        description=ResourceConfig.model_fields["resourceType"].description,
    )
    downloadUrl: Optional[HostlessAnyUrl] = Field(
        None,
        description=ResourceConfig.model_fields["downloadUrl"].description,
    )
    mediaType: Optional[str] = Field(
        None,
        description=ResourceConfig.model_fields["mediaType"].description,
    )
    storage_path: Annotated[
        Optional[str],
        Field(
            description="Path to metadata storage",
        ),
    ] = None
    collection_id: Annotated[
        Optional[str], Field(description="A reference to a DLite collection.")
    ] = None


class DLiteJsonStrategyConfig(ParserConfig):
    """DLite excel parse strategy  config."""

    configuration: Annotated[
        DLiteJsonParseConfig,
        Field(description="DLite json parse strategy-specific configuration."),
    ]


class DLiteJsonSessionUpdate(DLiteSessionUpdate):
    """Class for returning values from DLite json parser."""

    inst_uuid: Annotated[
        str,
        Field(
            description="UUID of new instance.",
        ),
    ]
    label: Annotated[
        str,
        Field(
            description="Label of the new instance in the collection.",
        ),
    ]


@dataclass
class DLiteJsonStrategy:
    """Parse strategy for Excel files.

    **Registers strategies**:

    - `("parserType",
        "json/vnd.dlite-json")`

    """

    parse_config: DLiteJsonStrategyConfig

    def initialize(self) -> DLiteSessionUpdate:
        """Initialize."""
        collection_id = (
            self.parse_config.configuration.collection_id
            or get_collection().uuid
        )
        return DLiteSessionUpdate(collection_id=collection_id)

    def get(self) -> DLiteJsonSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Returns:
            DLite instance.

        """
        config = self.parse_config.configuration
        try:
            # Update dlite storage paths if provided
            if config.storage_path:
                for storage_path in config.storage_path.split("|"):
                    dlite.storage_path.append(storage_path)
        except Exception as e:
            print(f"Error during update of DLite storage path: {e}")
            raise RuntimeError("Failed to update DLite storage path.") from e

        try:
            # Instantiate and use JSON parser from oteapi core
            json_parser = create_strategy(
                "parse",
                {
                    "parserType": "parser/json",
                    "entity": self.parse_config.entity,
                    "configuration": config,
                },
            )
            columns = json_parser.get()["content"]
        except Exception as e:
            # Handle errors that occur during JSON parser instantiation or
            # data retrieval. You can log the exception, raise a custom
            # exception, or handle it as needed. For example, logging the
            # error and raising a custom exception:
            print(f"Error during JSON parsing: {e}")
            raise RuntimeError("Failed to parse JSON data.") from e

        # Create DLite instance
        meta = get_meta(self.parse_config.entity)
        inst = meta(dimensions={})
        for name in list(columns.keys()):
            inst[name] = columns[name]

        # Add collection and add the entity instance
        coll = get_collection(
            collection_id=self.parse_config.configuration.collection_id
        )
        coll.add(config.label, inst)
        update_collection(coll)

        return DLiteJsonSessionUpdate(
            collection_id=coll.uuid,
            inst_uuid=inst.uuid,
            label=config.label,
        )
