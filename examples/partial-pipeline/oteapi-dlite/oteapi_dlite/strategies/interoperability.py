"""Dlite function strategy class."""
# pylint: disable=no-self-use,unused-argument
import pandas as pd
from typing import TYPE_CHECKING, List, Optional, Set, Tuple
from pydantic import Field, HttpUrl
from oteapi.models import AttrDict, FunctionConfig, SessionUpdate
from pydantic.dataclasses import dataclass
import dlite
import dlite.mappings as dm
from tripper import Triplestore
from oteapi_dlite.utils import get_collection
if TYPE_CHECKING:
    from typing import Any, Dict, Optional, List
RDFTriple = Tuple[str, str, str]


class TranslationConfig(AttrDict):
    """Pydantic model for the save collection function."""

    metadata: HttpUrl = Field(
        ...,
        description=(
            "URI of DLite metadata to return"
        ),
    )
    storage_path: str = Field(
        ...,
        description="Path to output_metadata storage",
    )
    fileDestination: Optional[str] = Field(
        ...,
        description=("Destination for saving the instance"),
    )


class TranslationFunctionFunctionConfig(FunctionConfig):
    """Function config."""

    configuration: TranslationConfig = Field(
        ...,
        description="save-collection-as-json-file configuration.",
    )


@dataclass
class TranslationFunctionStrategy:
    """Function Strategy.

    **Registers strategies**:

    - `("functionType", "dlite/translate)`

    """

    function_config: TranslationFunctionFunctionConfig

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

        return SessionUpdate()

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
        config = self.function_config.configuration
        coll = get_collection(session)
        ts = Triplestore(backend="rdflib")
        if coll.get_relations(p="http://emmo.info/domain-mappings#mapsTo"):
            ts.add_triples([
                [
                    ts.expand_iri(t) if isinstance(t, str) else t
                    for t in triple
                ]
                for triple in coll.get_relations(p="http://emmo.info/domain-mappings#mapsTo")
            ])
        # import pint
        # ureg=pint.UnitRegistry()
        # ureg.define("Celsius = 1 * celcius")

        # labels=config.input_labels
        # input_datamodel_list=[]
        # for label in labels:
        #     input_datamodel_list.append(coll[label])
        output_datamodel = dlite.Instance.from_location(
            'json', config.storage_path)
        print(output_datamodel)
        print("--------collection!!!!--------")
        print(coll)
        # Translate
        # inst=dm.instantiate(output_datamodel,input_datamodel_list,ts,quantity=ureg.Quantity,allow_incomplete=False)
        # coll.add(config.output_label, inst)
        import os
        instances = coll.get_instances(config.metadata, property_mappings=True)
        print(list(instances))
        # os.makedirs(os.path.dirname(config.fileDestination),
        #             exist_ok=True)
        # if config.fileDestination is not None:
        #     import json
            # for inst in instances:
            #     inst_dict = inst.asdict()['properties']
            #     with open(config.fileDestination ,mode="w+", encoding="UTF-8") as file:
            #         json.dump(inst_dict, file, indent=4)

       
        return SessionUpdate()
