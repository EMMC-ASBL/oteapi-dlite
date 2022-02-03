"""Demo mapping strategy class."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from typing import TYPE_CHECKING

from oteapi.plugins.factories import StrategyFactory

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from oteapi.models.mappingconfig import MappingConfig


@dataclass
@StrategyFactory.register(("mappingType", "mapping/DEMO"))
class DemoMappingStrategy:
    """Mapping Strategy."""

    mapping_config: "MappingConfig"

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "Dict[str, Any]":
        """Initialize strategy.

        This method will be called through the `/initialize` endpoint of the OTE-API
        Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            Dictionary of key/value-pairs to be stored in the sessions-specific
            dictionary context.

        """
        return {}

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> "Dict[str, Any]":
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint of the
        OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            Dictionary of key/value-pairs to be stored in the sessions-specific
            dictionary context.

        """
        return {}
