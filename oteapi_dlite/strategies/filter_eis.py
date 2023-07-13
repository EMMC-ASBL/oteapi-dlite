"""EIS filter strategy."""
# pylint: disable=unused-argument
from typing import TYPE_CHECKING, List, Optional

from oteapi.datacache import DataCache
from oteapi.models import AttrDict, DataCacheConfig, FilterConfig, SessionUpdate, ResourceConfig
from pydantic import Field
from pydantic.dataclasses import dataclass
from oteapi.plugins import create_strategy

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict

from galvani import BioLogic as BL
import pandas as pd


class EISConfig(AttrDict):
    """EIS parse-specific Configuration Data Model."""

    datacache_config: Optional[DataCacheConfig] = Field(
        None,
        description=(
            "Configurations for the data cache for storing the downloaded file "
            "content."
        ),
    )

class EISParseConfig(ResourceConfig):
    """File download strategy filter config."""
    
    datacache_config: Optional[DataCacheConfig] = Field(
        None,
        description=(
            "Configurations for the data cache for storing the downloaded file "
            "content."
        ),
    )

    configuration: EISConfig = Field(
        EISConfig(), description="EIS parse strategy-specific configuration."
    )



class SessionUpdateEIS(SessionUpdate):
    """Class for returning values from Download File strategy."""

    eis_data: dict = Field(..., description="Content of the EISDlite document.")


@dataclass
class EIS:
    """Filter Strategy.

    **Registers strategies**:

    - `("filterType", "filter/EIS")`

    """

    filter_config: EISConfig

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> SessionUpdate:
        """Initialize strategy.

        This method will be called through the `/initialize` endpoint of the OTEAPI
        Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            An update model of key/value-pairs to be stored in the
            session-specific context from services.

        """

        return SessionUpdate()

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdateEIS:

        if session["links"] is not None:
            links = session["links"]

            # find all EIS files in the folder
            eis_links = []
            for link in links:
                if link.endswith(".mpr") and "_PEIS_" in link:
                    eis_links.append(link)
                    continue

            # read data from the EIS files and create a DataFrame
            eis_data = None
            for eis_link in eis_links:
                config = {
                    "downloadUrl": eis_link,
                    "mediaType": "application/mpr"
                }
                downloader = create_strategy("download", config)
                session.update(downloader.initialize(session))
                downloader = create_strategy("download", config)
                output = downloader.get(session)
                session.update(output)

                # this fetches the key under which the file is stored in cache
                if "key" in output:
                    cache_key = output["key"]
                else:
                    raise RuntimeError("No data cache key provided to the downloaded content")

                # get access to cache
                cache = DataCache()
                
                # using the key get file from cache
                with cache.getfile(cache_key, suffix=".mpr") as filename:
                    mpr_file = BL.MPRfile(str(filename))

                eis_file_data = pd.DataFrame({
                    'EIS file': link.split("_")[-3],
                    'time/s': mpr_file.data['time/s'],
                    'Ewe/V': mpr_file.data['<Ewe>/V'],
                    'freq/Hz': mpr_file.data['freq/Hz'],
                    'Re(Z)/Ohm': mpr_file.data['Re(Z)/Ohm'],
                    '-Im(Z)/Ohm': mpr_file.data['-Im(Z)/Ohm'],
                    '|Z|/Ohm': mpr_file.data['|Z|/Ohm'],
                    'Phase(Z)/deg': mpr_file.data['Phase(Z)/deg'],
                })
                if eis_data is None:
                    eis_data = eis_file_data
                else:
                    # concatenate the data with previous EIS files' data
                    eis_data = pd.concat([eis_data, eis_file_data], ignore_index=True)


            print(eis_data)
            
            return SessionUpdateEIS(eis_data=eis_data.to_dict())
        else:
            raise RuntimeError("Dowload links not provided")



