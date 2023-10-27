"""Generic function strategy that converts zero or more input instances
to zero or more new output instances.

"""
# pylint: disable=unused-argument
import importlib
from typing import TYPE_CHECKING, Optional, Sequence

import dlite
from oteapi.models import AttrDict, FunctionConfig
from pydantic import Field
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection

if TYPE_CHECKING:
    from typing import Any, Dict


class DLiteConvertInputConfig(AttrDict):
    """Configuration for input instance to generic DLite converter.

    At least one of `label` or `datamodel` should be given.
    """

    label: Optional[str] = Field(
        None,
        description="Label of the instance.",
    )
    datamodel: Optional[str] = Field(
        None,
        description="URI of data model.",
    )
    property_mappings: bool = Field(
        False,
        description="Whether to infer instance from property mappings.",
    )


class DLiteConvertOutputConfig(AttrDict):
    """Configuration for output instance to generic DLite converter."""

    label: str = Field(
        None,
        description="Label to use when storing the instance.",
    )
    datamodel: Optional[str] = Field(
        None,
        description="URI of data model.  Used for documentation.",
    )


class DLiteConvertStrategyConfig(AttrDict):
    """Configuration for generic DLite converter."""

    function_name: str = Field(
        None,
        description="Name of convert function.  It will be pased the input "
        "instances as arguments and should return a sequence of output "
        "instances.",
    )
    module_name: str = Field(
        None,
        description="Name of Python module containing the convertion function.",
    )
    package: Optional[str] = Field(
        None,
        description="Used when performing a relative import of the converter "
        "function.  It specifies the package to use as the anchor point from "
        "which to resolve the relative import to an absolute import.",
    )
    pypi_package: Optional[str] = Field(
        None,
        description="Package name on PyPI.  This field is currently only "
        "informative, but might be used in the future for automatic package "
        "installation.",
    )
    inputs: Sequence[DLiteConvertInputConfig] = Field(
        None,
        description="Input instances.",
    )
    outputs: Sequence[DLiteConvertOutputConfig] = Field(
        None,
        description="Output instances.",
    )


class DLiteConvertConfig(FunctionConfig):
    """DLite convert strategy resource config."""

    configuration: DLiteConvertStrategyConfig = Field(
        ..., description="DLite convert strategy-specific configuration."
    )


@dataclass
class DLiteConvertStrategy:
    """Generic DLite convert strategy for converting zero or more input
    instances to zero or more output instances.

    **Registers strategies**:

    - `("functionType", "application/vnd.dlite-convert")`

    """

    convert_config: DLiteConvertConfig

    def initialize(
        self,
        session: "Optional[Dict[str, Any]]" = None,
    ) -> DLiteSessionUpdate:
        """Initialize."""
        return DLiteSessionUpdate(collection_id=get_collection(session).uuid)

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> DLiteSessionUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            SessionUpdate instance.
        """
        config = self.convert_config.configuration

        module = importlib.import_module(config.module_name, config.package)
        function = getattr(module, config.function_name)

        coll = get_collection(session)

        instances = []
        for i, input_config in enumerate(config.inputs):
            input_config = config.inputs[i]
            if input_config.label:
                instances.append(
                    coll.get(input_config.label, input_config.datamodel)
                )
            elif input_config.datamodel:
                inst = coll.get_instances(
                    metaid=input_config.datamodel,
                    property_mappings=input_config.property_mappings,
                    # More to do: add more arguments...
                )
            else:
                raise ValueError(
                    "either `label` or `datamodel` must be specified in "
                    "inputs[{i}]"
                )

        outputs = function(*instances)
        if isinstance(outputs, dlite.Instance):
            outputs = [outputs]

        for inst, output_config in zip(outputs, config.outputs):
            coll.add(output_config.label, inst)

        update_collection(coll)
        return DLiteSessionUpdate(collection_id=coll.uuid)


# DLiteConvertConfig.update_forward_refs()
