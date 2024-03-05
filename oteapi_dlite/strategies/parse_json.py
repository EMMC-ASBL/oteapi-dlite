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

    metadata: Annotated[
        Optional[HttpUrl],
        Field(
            description=(
                "URI of DLite metadata to return.  If not provided, the "
                "metadata will be inferred from the excel file."
            ),
        ),
    ] = None

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


class DLiteJsonParseConfig(ParserConfig):
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

    parse_config: DLiteJsonParseConfig

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

        config1 = self.parse_config.model_dump()
        config1["configuration"] = config
        config1["parserType"] = (
            "parser/json"
        )
        parser: "IParseStrategy" = JSONDataParseStrategy(config1)
        columns: dict[str, "Any"] = parser.get()['content']
        
        
        meta = get_meta(self.parse_config.entity)
        inst = meta(dimensions={})
        names=list(columns.keys())

        for name in names:
            inst[name] = columns[name]
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

