"""Generic strategy for adding configurations to the session."""

# pylint: disable=unused-argument,invalid-name
from typing import TYPE_CHECKING, Annotated, Optional, Union

from oteapi.models import AttrDict, FilterConfig, SessionUpdate
from pydantic import Field
from pydantic.dataclasses import dataclass

# from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import add_settings

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


# Must add this explicitly to make mypy happy
NoneType = type(None)


class SettingsConfig(AttrDict):
    """Configuration for a generic "settings" filter.

    This strategy stores settings in the session such that they are
    available for other strategies later in the pipeline.

    The settings are stored as a JSON string and can be accessed
    by its label.

    """

    label: Annotated[
        str,
        Field(
            description=(
                "Label for accessing this configuration.  "
                "It should be unique."
            ),
        ),
    ]
    settings: Annotated[
        Union[dict, list, str, int, float, bool, NoneType],
        Field(
            description=(
                "The configurations to store, represented as a Python "
                "object that can be serialised to JSON."
            ),
        ),
    ]


class SettingsFilterConfig(FilterConfig):
    """Settings strategy config."""

    configuration: Annotated[
        SettingsConfig,
        Field(description="Settings strategy-specific configuration."),
    ]


@dataclass
class SettingsStrategy:
    """Generic settings strategy for storing settings for other
    strategies.

    **Registers strategies**:

    - `("mediaType", "application/vnd.dlite-settings")`

    """

    settings_config: SettingsFilterConfig

    def initialize(
        self,
        session: Optional[dict[str, "Any"]] = None,
    ) -> SessionUpdate:
        """Store settings."""
        config = self.settings_config.configuration
        return add_settings(session, config.label, config.settings)

    def get(self, session: Optional[dict[str, "Any"]] = None) -> SessionUpdate:
        """Do nothing."""
        return SessionUpdate()