"""Strategy that parses resource id and return all associated download links."""
import requests
import json

from pydantic import Field
from pydantic.dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict

from oteapi.models import AttrDict, DataCacheConfig, ResourceConfig, SessionUpdate
from oteapi.plugins import create_strategy

from galvani import BioLogic as BL


class MPRConfig(AttrDict):
    """MPR parse-specific Configuration Data Model."""

    datacache_config: Optional[DataCacheConfig] = Field(
        None,
        description=(
            "Configurations for the data cache for storing the downloaded file "
            "content."
        ),
    )

class MPRParseConfig(ResourceConfig):
    """File download strategy filter config."""

    mediaType: str = Field(
        "application/mpr",
        const=True,
        description=ResourceConfig.__fields__["mediaType"].field_info.description,
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

    links: list = Field(..., description="Content of the MPR document.")


@dataclass
class MPRDataParseStrategy:
    """Parse strategy for MPR.

    **Registers strategies**:

    - `("mediaType", "application/mpr")`

    """

    parse_config: MPRParseConfig

    def initialize(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Initialize."""
        return SessionUpdate()

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdateMPRParse:
        """Download mpr file and return a list of dowload urls for later analysis."""

        config = self.parse_config
        request = requests.get(config.downloadUrl)
        resource = json.loads(request.text)["results"][0]

        links = []
        if "distributions" in resource:
            if len(resource["distributions"]) > 0:
                for distribution in resource["distributions"]:
                    if "downloadURL" in distribution:
                        links.append(distribution["downloadURL"])
            else:
                raise ValueError(
                    "Distributions are empty."
                )
        else:
            raise ValueError(
                "Expected the parse strategy to recieve a list of distributions with a content key."
            )

        return SessionUpdateMPRParse(links=links)
