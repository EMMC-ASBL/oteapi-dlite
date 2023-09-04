"""Strategy that parses resource id and return all associated download links."""
from typing import Any, Dict, Optional

import dlite
import pandas as pd
import requests  # type: ignore
from galvani import BioLogic as BL
from oteapi.datacache import DataCache
from oteapi.models import (
    AttrDict,
    DataCacheConfig,
    ResourceConfig,
    SessionUpdate,
)
from pydantic import Field, HttpUrl
from pydantic.dataclasses import dataclass

from oteapi_dlite.utils import dict2recarray, get_collection, update_collection


class MPRConfig(AttrDict):
    """MPR parse-specific Configuration Data Model."""

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
        "mpr-data",
        description="Optional label for new instance in collection.",
    )

    mpr_config: AttrDict = Field(
        AttrDict(),
        description="Co .",
    )
    storage_path: Optional[str] = Field(
        None,
        description="Path to metadata storage",
    )


class MPRParseConfig(ResourceConfig):
    """File download strategy filter config."""

    mediaType: str = Field(
        "application/parse-mpr",
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

    configuration: MPRConfig = Field(
        MPRConfig(), description="MPR parse strategy-specific configuration."
    )


class SessionUpdateMPRParse(SessionUpdate):
    """Class for returning values from MPR Parse."""

    eis_data: dict = Field(..., description="Content of the EISDlite document.")


@dataclass
class MPRDataParseStrategy:
    """Parse strategy for MPR.

    **Registers strategies**:

    - `("mediaType", "application/parse-mpr")`

    """

    parse_config: MPRParseConfig

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> SessionUpdate:
        """Initialize."""
        return SessionUpdate()

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> SessionUpdateMPRParse:
        """Download mpr file and return a list of dowload urls for later analysis."""
        coll = get_collection(session)
        config = self.parse_config
        relations = config.configuration.mpr_config
        # print(config.configuration.mpr_config)
        req = requests.get(
            config.downloadUrl,
            allow_redirects=True,
            timeout=(3, 27),  # timeout: (connect, read) in seconds
        )
        cache = DataCache()
        key = cache.add(req.content)
        # using the key get file from cache
        with cache.getfile(key, suffix=".mpr") as filename:
            mpr_file = BL.MPRfile(str(filename))
        data = {}
        for relation in relations:
            data[relation] = mpr_file.data[relations[relation]]
        eis_file_data = pd.DataFrame(data)
        eis_data = None
        if eis_data is None:
            eis_data = eis_file_data
        else:
            # concatenate the data with previous EIS files' data
            eis_data = pd.concat([eis_data, eis_file_data], ignore_index=True)
        rec = dict2recarray(data)
        configuration = config.configuration
        if configuration.metadata:
            if configuration.storage_path is not None:
                for storage_path in configuration.storage_path.split("|"):
                    dlite.storage_path.append(storage_path)
            meta = dlite.get_instance(configuration.metadata)

        inst = meta(dims=[len(rec)], id=configuration.id)
        for name in relations:
            inst[name] = data[name]
        # # Insert inst into collection
        coll.add(configuration.label, inst)
        update_collection(coll)
        print(coll)
        return SessionUpdateMPRParse(eis_data=eis_data.to_dict())
