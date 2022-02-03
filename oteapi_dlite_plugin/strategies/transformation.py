"""Demo transformation strategy class."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from oteapi.models.transformationconfig import TransformationStatus
from oteapi.plugins.factories import StrategyFactory

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from oteapi.models.transformationconfig import TransformationConfig


@dataclass
@StrategyFactory.register(("transformation_type", "script/DEMO"))
class DummyTransformationStrategy:
    """Transformation Strategy."""

    transformation_config: "TransformationConfig"

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
        return {"result": "collection id"}

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

    def run(self, session: "Optional[Dict[str, Any]]" = None) -> "Dict[str, Any]":
        """Run a transformation job.

        This method will be called through the `/initialize` endpoint of the OTE-API
        Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            Dictionary of key/value-pairs to be stored in the sessions-specific
            dictionary context.
            As a minimum, the dictionary will contain the job ID.

        """
        return {"result": "a01d"}

    def status(self, task_id: str) -> TransformationStatus:
        """Get job status.

        Parameters:
            task_id: The transformation job ID.

        Returns:
            An overview of the transformation job's status, including relevant
            metadata.

        """
        return TransformationStatus(
            id=task_id,
            status="wip",
            messages=[],
            created=datetime.utcnow(),
            startTime=datetime.utcnow(),
            finishTime=datetime.utcnow(),
            priority=0,
            secret=None,
            configuration={},
        )
