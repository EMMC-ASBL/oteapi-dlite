"""Demo filter strategy."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from oteapi.plugins.factories import StrategyFactory
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from oteapi.models.filterconfig import FilterConfig


class DemoDataModel(BaseModel):
    """Demo filter data model."""

    demo_data: List[int] = Field([], description="List of demo data.")


@dataclass
@StrategyFactory.register(("filterType", "filter/DEMO"))
class DemoFilter:
    """Filter Strategy."""

    filter_config: "FilterConfig"

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
        return {"result": "collectionid"}

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
        model = DemoDataModel(**self.filter_config.configuration)
        return {"key": model.demo_data}
