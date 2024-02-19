"""Strategy for parsing an Excel spreadsheet to a DLite instance."""

# pylint: disable=unused-argument
import re
from random import getrandbits
from typing import TYPE_CHECKING, Annotated, Optional

import dlite
import numpy as np
from dlite.datamodel import DataModel
from oteapi.models import AttrDict, ResourceConfig
from oteapi.strategies.parse.excel_xlsx import (
    XLSXParseConfig,
    XLSXParseStrategy,
)
from pydantic import Field, HttpUrl
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import dict2recarray, get_collection, update_collection

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Union

    from oteapi.interfaces import IParseStrategy


class DLiteExcelParseConfig(AttrDict):
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


class DLiteExcelParseResourceConfig(ResourceConfig):
    """DLite excel parse strategy resource config."""

    configuration: Annotated[
        DLiteExcelParseConfig,
        Field(description="DLite excel parse strategy-specific configuration."),
    ]


class DLiteExcelSessionUpdate(DLiteSessionUpdate):
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

    parse_config: DLiteExcelParseResourceConfig

    def initialize(
        self,
        session: Optional[dict[str, "Any"]] = None,
    ) -> DLiteSessionUpdate:
        """Initialize."""
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)

    def get(
        self, session: Optional[dict[str, "Any"]] = None
    ) -> DLiteExcelSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            DLite instance.

        """
        config = self.parse_config.configuration

        xlsx_config = self.parse_config.model_dump()
        xlsx_config["configuration"] = config.excel_config
        xlsx_config["mediaType"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        parser: "IParseStrategy" = XLSXParseStrategy(xlsx_config)
        columns: dict[str, "Any"] = parser.get(session)["data"]

        names, units = zip(
            *[split_column_name(column) for column in columns.keys()]
        )
        rec = dict2recarray(columns, names=names)

        if not isinstance(units, (list, tuple)):
            # This check is to satisfy mypy for the `infer_metadata` call below.
            raise TypeError(
                f"units must be a list or tuple, instead it was {type(units)}"
            )

        if config.metadata:
            if config.storage_path is not None:
                for storage_path in config.storage_path.split("|"):
                    dlite.storage_path.append(storage_path)
            meta = dlite.get_instance(config.metadata)
            # check the metadata config would go here
        else:
            meta = infer_metadata(rec, units=units)

        inst = meta(dimensions=[len(rec)], id=config.id)
        for name in names:
            inst[name] = rec[name]

        # Insert inst into collection
        coll = get_collection(session)
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
