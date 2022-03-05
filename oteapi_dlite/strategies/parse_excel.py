"""Strategy for parsing an Excel spreadsheet to a DLite instance."""
# pylint: disable=no-self-use,unused-argument
import re
from dataclasses import dataclass
from random import getrandbits
from typing import TYPE_CHECKING, Optional

import dlite
import numpy as np
from dlite.datamodel import DataModel
from oteapi.models import AttrDict, ResourceConfig, SessionUpdate
from oteapi.strategies.parse.excel_xlsx import XLSXParseConfig, XLSXParseStrategy
from pydantic import Field, HttpUrl

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import dict2recarray

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.interfaces import IParseStrategy


class DLiteExcelParseConfig(AttrDict):
    """Configuration for DLite Excel parser."""

    metadata: Optional[HttpUrl] = Field(
        None,
        description=(
            "URI of DLite metadata to return.  If not provided, the metadata "
            "will be inferred from the excel file."
        ),
    )

    id: Optional[str] = Field(None, description="Optional id on new instance.")

    label: Optional[str] = Field(
        "excel-data",
        description="Optional label for new instance in collection.",
    )

    excel_config: XLSXParseConfig = Field(
        ...,
        description="DLite-specific excel configurations.",
    )


class DLiteExcelParseResourceConfig(ResourceConfig):
    """DLite excel parse strategy resource config."""

    configuration: DLiteExcelParseConfig = Field(
        ..., description="DLite excel parse strategy-specific configuration."
    )


class DLiteExcelSessionUpdate(DLiteSessionUpdate):
    """Class for returning values from DLite excel parser."""

    inst_uuid: str = Field(
        ...,
        description="UUID of new instance.",
    )
    label: str = Field(
        ...,
        description="Label of the new instance in the collection.",
    )


@dataclass
class DLiteExcelStrategy:
    """Parse strategy for Excel files.

    **Registers strategies**:

    - `("mediaType", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")`

    """

    parse_config: "ResourceConfig"

    def initialize(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Initialize."""
        if session is None:
            raise ValueError("Missing session")
        return DLiteSessionUpdate(collection_id=session["collection_id"])

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint of the
        OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            DLite instance.

        """
        if session is None:
            raise ValueError("Missing session")

        config = DLiteExcelParseConfig(**self.parse_config.configuration)

        xlsx_session = self.parse_config.copy()
        xlsx_session.configuration = config.excel_config
        parser: "IParseStrategy" = XLSXParseStrategy(xlsx_session)
        columns = parser.get(session)["data"]

        names, units = zip(*[split_column_name(column) for column in columns])
        rec = dict2recarray(columns, names=names)

        if config.metadata:
            raise NotImplementedError("")
        # else
        meta = infer_metadata(rec, units=units)

        inst = meta(dims=[len(rec)], id=config.id)
        for name in names:
            inst[name] = rec[name]

        # Insert inst into collection
        coll: dlite.Collection = dlite.get_collection(session["collection_id"])
        coll.add(config.label, inst)

        # Increase refcount of instance to avoid that it is freed when
        # returning from this function
        inst.incref()

        return DLiteExcelSessionUpdate(
            collection_id=coll.uuid,
            inst_uuid=inst.uuid,
            label=config.label,
        )


def split_column_name(column):
    """Split column name into a (name, unit) tuple."""
    match = re.match(r"\s*([^ ([<]+)\s*[([<]?([^] )>]*)[])>]?", column)
    if not match:
        return column, ""
    name, unit = match.groups()
    return name, unit


def infer_metadata(rec: np.recarray, units: list) -> dlite.Instance:
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
        metadata.add_property(name, type=ptype, dims=["nrows"], unit=units[i])
    return metadata.get()
