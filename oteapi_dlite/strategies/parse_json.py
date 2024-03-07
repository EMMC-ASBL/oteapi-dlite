"""Strategy for JSON parsing."""

# pylint: disable=unused-argument
from typing import TYPE_CHECKING, Annotated, Optional

import dlite
from oteapi.models import AttrDict, ParserConfig
from oteapi.plugins import create_strategy
from pydantic.dataclasses import dataclass
from pydantic import Field

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection
from oteapi_dlite.utils.utils import get_meta


if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Union


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
        if self.parse_config.configuration.collection_id:
            return DLiteSessionUpdate(
                collection_id=self.parse_config.configuration.collection_id
            )
        return DLiteSessionUpdate(collection_id=get_collection().uuid)

    def get(self) -> DLiteJsonSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

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
                "parse", {
                    "parserType": "parser/json", 
                    "entity": self.parse_config.entity,
                    "configuration": config}
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
