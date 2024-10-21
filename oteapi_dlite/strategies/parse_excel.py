"""Strategy for parsing an Excel spreadsheet to a DLite instance."""

from __future__ import annotations

import re
import sys
from random import getrandbits
from typing import TYPE_CHECKING, Annotated, Optional

if sys.version_info >= (3, 9, 1):
    from typing import Literal
else:
    from typing_extensions import Literal  # type: ignore[assignment]

import dlite
import numpy as np
from dlite.datamodel import DataModel
from oteapi.models import HostlessAnyUrl, ParserConfig, ResourceConfig
from oteapi.plugins import create_strategy
from oteapi.strategies.parse.excel_xlsx import XLSXParseConfig
from pydantic import AnyHttpUrl, Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteResult
from oteapi_dlite.utils import dict2recarray, get_collection, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class DLiteExcelParseConfig(DLiteResult):
    """Configuration for DLite Excel parser."""

    # Resource config
    downloadUrl: Annotated[
        Optional[HostlessAnyUrl],
        Field(
            description=ResourceConfig.model_fields["downloadUrl"].description
        ),
    ] = None

    mediaType: Annotated[
        Literal[
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ],
        Field(description=ResourceConfig.model_fields["mediaType"].description),
    ] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # Parser config
    id: Annotated[
        Optional[str], Field(description="Optional id on new instance.")
    ] = None

    label: Annotated[
        Optional[str],
        Field(
            description="Optional label for new instance in collection.",
        ),
    ] = "excel-data"

    excel_config: Annotated[
        XLSXParseConfig,
        Field(
            description="DLite-specific excel configurations.",
        ),
    ]
    storage_path: Annotated[
        Optional[str],
        Field(
            description="Path to metadata storage",
        ),
    ] = None


class DLiteExcelParserConfig(ParserConfig):
    """DLite excel parse strategy resource config."""

    parserType: Annotated[
        Literal["application/vnd.dlite-xlsx"],
        Field(description=ParserConfig.model_fields["parserType"].description),
    ] = "application/vnd.dlite-xlsx"
    configuration: Annotated[
        DLiteExcelParseConfig,
        Field(description="DLite excel parse strategy-specific configuration."),
    ]
    entity: Annotated[
        Optional[AnyHttpUrl],
        Field(
            description=(
                "URI of DLite metadata to return. If not provided, the "
                "metadata will be inferred from the excel file."
            ),
        ),
    ] = None


class DLiteExcelSessionUpdate(DLiteResult):
    """Class for returning values from DLite excel parser."""

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
class DLiteExcelStrategy:
    """Parse strategy for Excel files.

    **Registers strategies**:

    - `("mediaType",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")`

    """

    parse_config: DLiteExcelParserConfig

    def initialize(self) -> DLiteResult:
        """Initialize."""
        return DLiteResult(
            collection_id=get_collection(
                self.parse_config.configuration.collection_id
            ).uuid
        )

    def get(self) -> DLiteExcelSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Returns:
            DLite instance.

        """
        config = self.parse_config.configuration

        if config.downloadUrl is None:
            raise ValueError("downloadUrl is required.")
        if config.mediaType is None:
            raise ValueError("mediaType is required.")

        xlsx_config = {
            "parserType": "parser/excel_xlsx",
            "configuration": config.excel_config.model_dump(),
            "entity": (
                self.parse_config.entity
                if self.parse_config.entity
                else "https://example.org"
            ),
        }
        xlsx_config["configuration"].update(
            {
                "downloadUrl": config.downloadUrl,
                "mediaType": config.mediaType,
            }
        )
        parser = create_strategy("parse", xlsx_config)
        columns: dict[str, Any] = parser.get()["data"]

        names, units = zip(*[split_column_name(column) for column in columns])
        rec = dict2recarray(columns, names=names)

        if not isinstance(units, (list, tuple)):
            # This check is to satisfy mypy for the `infer_metadata` call below.
            raise TypeError(
                f"units must be a list or tuple, instead it was {type(units)}"
            )

        meta_uri = self.parse_config.entity
        if meta_uri:
            if config.storage_path is not None:
                for storage_path in config.storage_path.split("|"):
                    dlite.storage_path.append(storage_path)
            meta = dlite.get_instance(str(meta_uri))
            # check the metadata config would go here
        else:
            meta = infer_metadata(rec, units=units)

        inst = meta(dimensions=[len(rec)], id=config.id)
        for name in names:
            inst[name] = rec[name]

        # Insert inst into collection
        coll = get_collection(config.collection_id)
        coll.add(config.label, inst)

        update_collection(coll)
        return DLiteExcelSessionUpdate(
            collection_id=coll.uuid,
            inst_uuid=inst.uuid,
            label=config.label,
        )


def split_column_name(column: str) -> tuple[str, str]:
    """Split column name into a (name, unit) tuple."""
    match = re.match(r"\s*([^ ([<]+)\s*[([<]?([^] )>]*)[])>]?", column)
    if not match:
        return column, ""
    name, unit = match.groups()
    return name, unit


def infer_metadata(rec: np.recarray, units: tuple[str, ...]) -> dlite.Instance:
    """Infer dlite metadata from recarray `rec`."""
    rnd = getrandbits(128)
    uri = f"http://onto-ns.com/meta/1.0/generated_from_excel_{rnd:0x}"
    metadata = DataModel(
        uri,
        description="Generated datamodel from excel file.",
    )
    metadata.add_dimension("nrows", "Number of rows.")
    for i, name in enumerate(rec.dtype.names):
        dtype = rec[name].dtype
        ptype = "string" if dtype.kind == "U" else dtype.name
        metadata.add_property(name, type=ptype, shape=["nrows"], unit=units[i])
    return metadata.get()
