"""Dlite function strategy class."""
# pylint: disable=no-self-use,unused-argument
import pandas as pd
import re
import dlite
from  tempfile import NamedTemporaryFile 
from typing import TYPE_CHECKING
from pydantic import Field
from oteapi.models import AttrDict, FunctionConfig, SessionUpdate
from oteapi.datacache import DataCache
from pydantic.dataclasses import dataclass
from oteapi_dlite.models import DLiteSessionUpdate
import numpy as np
if TYPE_CHECKING:
    from typing import Any, Dict, Optional

class SaveCollectionAsJSONConfig(AttrDict):
    """Pydantic model for the save collection function."""

    file_storage_path: str = Field(
        ...,
        description="Path to store collection (JSON file)",
    
    )
    label: str = Field(
        ...,
        description="Label for output instances in collection.",
    )

class SaveCollectionAsJSONFunctionConfig(FunctionConfig):
    """Function config."""

    configuration: SaveCollectionAsJSONConfig = Field(
        ...,
        description="save-collection-as-json-file configuration.",
    )
    
class DLiteSaveCollectionSessionUpdate(DLiteSessionUpdate):
    """Class for returning values from DLite excel parser."""

    data: dict = Field(
        ...,
        description="UUID of new instance.",
    )
    

@dataclass
class SaveCollectionAsJSONFunctionStrategy:
    """Function Strategy.

    **Registers strategies**:

    - `("functionType", "dlite/saveCollectionAsJSON)`

    """

    function_config: SaveCollectionAsJSONFunctionConfig

    def initialize(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Initialize strategy.

        This method will be called through the `/initialize` endpoint of the OTEAPI
        Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            An update model of key/value-pairs to be stored in the
            session-specific context from services.

        """
        if session is None:
            raise ValueError("Missing session")
        return DLiteSessionUpdate(collection_id=session["collection_id"])

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint of the
        OTEAPI Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            An update model of key/value-pairs to be stored in the
            session-specific context from services.

        """
        if session is None:
            raise ValueError("Missing session")        
        coll: dlite.Collection = dlite.get_collection(session['collection_id'])  
              
        coll.save(f'json:{self.function_config.configuration.file_storage_path}coll.json?mode=w')
        
        instance=coll[self.function_config.configuration.label]
        # print(instance)
        # import pandas as pd
        # df = pd.DataFrame(data=instance.properties)
        # items=df.to_json(orient = 'columns')
        # data={}
        # for item1 in items:
        #     data[item1]=list((items[item1]).values())
            
        return DLiteSaveCollectionSessionUpdate(data=data,collection_id=session["collection_id"])

