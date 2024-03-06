"""Strategy for parsing an Excel spreadsheet to a DLite instance."""

# pylint: disable=unused-argument
from typing import TYPE_CHECKING, Annotated, Optional

import dlite
from oteapi.models import AttrDict, ParserConfig
from oteapi.strategies.parse.application_json import (
    JSONParserConfig,
    JSONDataParseStrategy,
)
from pydantic import Field, HttpUrl
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import dict2recarray, get_collection, update_collection
from oteapi_dlite.utils.utils import get_meta

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Union

    from oteapi.interfaces import IParseStrategy


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

    storagePath: Annotated[
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
        collection_id = self.parse_config.collection_id or get_collection().uuid
        return DLiteSessionUpdate(collection_id=collection_id)

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

        # Update dlite storage paths if provided
        if config.storagePath:
            for storage_path in config.storage_path.split("|"):
                dlite.storage_path.append(storage_path)

        # Instantiate and use JSON parser
        json_parser_config = {
            "configuration": config.dict(),
            "parserType": "parser/json",
        }
        json_parser = JSONDataParseStrategy(json_parser_config)
        columns = json_parser.get()["content"]

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
