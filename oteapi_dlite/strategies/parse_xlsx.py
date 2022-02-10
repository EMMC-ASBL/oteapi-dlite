"""Strategy class for parsing xlsx to a DLite instance."""
# pylint: disable=no-self-use,unused-argument
import re
from dataclasses import dataclass
from random import getrandbits
from typing import TYPE_CHECKING, Optional

import dlite
import numpy as np
from dlite.datamodel import DataModel
from oteapi.datacache.datacache import DataCache
from oteapi.strategies.parse.excel_xlsx import XLSXParseDataModel, XLSXParseStrategy
from pydantic import BaseModel, Field, HttpUrl

from oteapi_dlite.utils import dict2recarray

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

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
        return {}

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> "Dict[str, Any]":
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint of the
        OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            DLite instance.

        """
        config = DLiteXLSXConfig(**self.parse_config.configuration)
        parse_config = self.parse_config.copy()
        parse_config.configuration = config.xlsx_config.dict()

        parser = XLSXParseStrategy(parse_config)
        columns = parser.get(session)

        with open("xxx.py", "w") as f:
            print(repr(columns), file=f)

        names, units = zip(*[split_column_name(column) for column in columns])
        rec = dict2recarray(columns, names=names)

        if config.metadata:
            raise NotImplementedError("")
        else:
            meta = infer_metadata(rec, units=units)

        inst = meta(dims=[len(rec)], id=config.id)
        for name in names:
            inst[name] = rec[name]

        inst.incref()
        return {"uuid": inst.uuid}


def split_column_name(column):
    """Split column name into a (name, unit) tuple."""
    match = re.match(r"\s*([^ ([<]+)\s*[([<]?([^] )>]*)[])>]?", column)
    if not match:
        return column, ""
    name, unit = match.groups()
    return name, unit


def infer_metadata(rec: dict, units: list) -> "dlite.Instance":
    """Infer dlite metadata from recarray `rec`."""
    rnd = getrandbits(128)
    uri = f"http://onto-ns.com/meta/1.0/generated_from_xlsx_{rnd:0x}"
    metadata = DataModel(uri, description="Generated datamodel from xlsx file.")
    metadata.add_dimension("nrows", "Number of rows.")
    for i, name in enumerate(rec.dtype.names):
        dtype = rec[name].dtype
        metadata.add_property(name, type=dtype.name, dims=["nrows"], unit=units[i])
    return metadata.get()
