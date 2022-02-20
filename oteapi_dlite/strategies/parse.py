"""Strategy class for parsing xlsx to a DLite instance."""
# pylint: disable=no-self-use,unused-argument
import re
from dataclasses import dataclass
from random import getrandbits
from typing import TYPE_CHECKING, Optional

import dlite
import numpy as np
from dlite.datamodel import DataModel
from oteapi.models import SessionUpdate
from oteapi.strategies.parse.excel_xlsx import XLSXParseDataModel, XLSXParseStrategy
from pydantic import BaseModel, Field, HttpUrl

from oteapi_dlite.utils import dict2recarray

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.models.resourceconfig import ResourceConfig


class DLiteXLSXConfig(BaseModel):
    """Configuration for DLite XLSX parser."""

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

    xlsx_config: XLSXParseDataModel = Field(
        ...,
        description="Excel XLSX configurations.",
    )


@dataclass
class DLiteXLSXParseStrategy:
    """Parse strategy for Excel XLSX files.

    **Registers strategies**:

    - `("mediaType", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")`

    """

    parse_config: "ResourceConfig"

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "Dict[str, Any]":
        """Initialize."""
        return SessionUpdate()

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> "Dict[str, Any]":
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

        config = DLiteXLSXConfig(**self.parse_config.configuration)
        parse_config = self.parse_config.copy()
        parse_config.configuration = config.xlsx_config.dict()

        parser = XLSXParseStrategy(parse_config)
        columns = parser.get(session)["data"]

        names, units = zip(*[split_column_name(column) for column in columns])
        rec = dict2recarray(columns, names=names)

        if config.metadata:  # pylint: disable=no-else-raise
            raise NotImplementedError("")
        else:
            meta = infer_metadata(rec, units=units)

        inst = meta(dims=[len(rec)], id=config.id)
        for name in names:
            inst[name] = rec[name]

        # Insert inst into collection
        coll = dlite.get_collection(session["collection_id"])
        coll.add(config.label, inst)

        # Increase refcount of instance to avoid that it is freed when
        # returning from this function
        inst.incref()

        return SessionUpdate(
            inst_uuid=inst.uuid,
            collection_id=coll.uuid,
            label=config.label,
        )


def split_column_name(column):
    """Split column name into a (name, unit) tuple."""
    match = re.match(r"\s*([^ ([<]+)\s*[([<]?([^] )>]*)[])>]?", column)
    if not match:
        return column, ""
    name, unit = match.groups()
    return name, unit


def infer_metadata(rec: np.recarray, units: list) -> "dlite.Instance":
    """Infer dlite metadata from recarray `rec`."""
    rnd = getrandbits(128)
    uri = f"http://onto-ns.com/meta/1.0/generated_from_xlsx_{rnd:0x}"
    metadata = DataModel(uri, description="Generated datamodel from xlsx file.")
    metadata.add_dimension("nrows", "Number of rows.")
    for i, name in enumerate(rec.dtype.names):
        dtype = rec[name].dtype
        ptype = "string" if dtype.kind == "U" else dtype.name
        metadata.add_property(name, type=ptype, dims=["nrows"], unit=units[i])
    return metadata.get()
