"""Strategy class for saving a DLite Instance or Collection to file."""
# pylint: disable=unused-argument,too-many-statements, too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=W0612,W0611,W0511

import json
import os
from typing import TYPE_CHECKING, Dict, Optional

import dlite
from oteapi.models import AttrDict, FunctionConfig, SessionUpdate
from pydantic import Field
from pydantic.dataclasses import dataclass
from oteapi_dlite.utils import get_collection


if TYPE_CHECKING:
    from typing import Any


class InstanceSaveConfig(AttrDict):
    """Pydantic model for the Instance Save."""

    fileDestination: str = Field(
        ...,
        description=("Destination for saving the instance"),
    )
    label: str = Field(
        ...,
        description=("label to fetch"),
    )

    instanceId: Optional[str] = Field(
        "",
        description=("Id of instance to save")
    )

    instanceKey: Optional[str] = Field(
        "",
        description=("Session key of instance to save")
    )

    format: Optional[str] = Field(
        "instance",
        description=("Selection of the format, either instance or collection")
    )


class InstanceSaveFunctionConfig(FunctionConfig):
    """File save strategy filter config."""

    configuration: InstanceSaveConfig = Field(
        ...,
        description="Instance save strategy-specific configuration.",
    )


class SessionUpdateInstanceSave(SessionUpdate):
    """Class for returning values from Instance Save."""


@dataclass
class InstanceSaveStrategy:
    """Save strategy for DLites instance

    **Registers strategies**:

    - `("functionType", "function/saveInstance")`

    """

    save_config: InstanceSaveFunctionConfig

    def initialize(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Initialize."""
        return SessionUpdate()

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Parse Instance.
        Arguments:
            session: A session-specific dictionary context.

        Returns:
            instance_key_dict: dict of instance keys/labels
        """
        # Check for session:
        if session is None:
            raise Exception("Missing session")

        # if self.save_config.configuration.instanceId == "":
        #     if self.save_config.configuration.instanceKey != "":
        #         if self.save_config.configuration.instanceKey in session:
        #             instance_id = session[self.save_config.configuration.instanceKey]
        #         else:
        #             raise Exception("instanceKey not in session!: ",
        #                                     self.save_config.configuration.instanceKey)
        #     else:
        #         if "collection_id" in session:
        #             instance_id = session["collection_id"]
        #         else:
        #             raise Exception("Collection_id not in session!")
        # else:
        #     instance_id = self.save_config.configuration.instanceId

        try:
            # inst = dlite.get_instance(instance_id)
            coll=get_collection(session)
            inst=coll[self.save_config.configuration.label]
        except dlite.DLiteError as error:
            raise Exception("Could not get instance! " + repr(error)) from error

        if self.save_config.configuration.format == "dlitesave":
            inst_dict = json.loads(inst.asjson())
            # Create the directory if it does not exist
            os.makedirs(os.path.dirname(self.save_config.configuration.fileDestination),
                                    exist_ok=True)
            inst.save('json://'+self.save_config.configuration.fileDestination+'?mode=w')
        else:
            if self.save_config.configuration.format == "instance":
                inst_dict = inst.asdict()['properties']
            elif self.save_config.configuration.format == "collection":
                dict0 = inst.asdict()
                dict0.pop('uuid', None)
                inst_dict = {}
                inst_dict[inst.uuid] = dict0
            else:
                raise Exception("Format need to be either instance"
                                    " or collection, got instead: "
                                    + str(self.save_config.configuration.format))

            # Create the directory if it does not exist
            os.makedirs(os.path.dirname(self.save_config.configuration.fileDestination),
                                        exist_ok=True)

            # Save the instance in a file
            with open(self.save_config.configuration.fileDestination, mode="w+",
                        encoding="UTF-8") as file:
                json.dump(inst_dict,file,indent=4)

        return SessionUpdateInstanceSave(
            **{
            },
        )
