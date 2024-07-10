"""Strategy for oceanlab data parsing from Influx DB."""

import logging
import sys
from typing import Annotated, Optional

import cachetools  # type: ignore
import dlite
import influxdb_client
import jinja2
from oteapi.models import AttrDict, HostlessAnyUrl, ParserConfig, ResourceConfig
from pandas import DataFrame
from pydantic import BaseModel, Field, SecretStr
from pydantic.dataclasses import dataclass

from oteapi_dlite.models import DLiteSessionUpdate
from oteapi_dlite.utils import get_collection, update_collection
from oteapi_dlite.utils.utils import get_meta

if sys.version_info >= (3, 10):
    from typing import Literal
else:
    from typing_extensions import Literal
logger = logging.getLogger(__name__)


class Measurement(BaseModel):
    """Measurement and field value from the Influx DB"""

    measurement: Annotated[str, Field(description="The measurement name")]
    field: Annotated[
        str, Field(description="The measurement's field in the DB")
    ]


class InfluxParseParseConfig(AttrDict):
    """Configuration for DLite Excel parser."""

    id: Annotated[
        Optional[str], Field(description="Optional id on new instance.")
    ] = None

    label: Annotated[
        Optional[str],
        Field(
            description="Optional label for new instance in collection.",
        ),
    ] = "json-data"

    resourceType: Annotated[
        Optional[Literal["resource/url"]],
        Field(
            description=ResourceConfig.model_fields["resourceType"].description,
        ),
    ] = "resource/url"
    downloadUrl: Annotated[
        Optional[HostlessAnyUrl],
        Field(
            description=ResourceConfig.model_fields["downloadUrl"].description,
        ),
    ] = None
    mediaType: Annotated[
        Optional[str],
        Field(
            description=ResourceConfig.model_fields["mediaType"].description,
        ),
    ] = None
    storage_path: Annotated[
        Optional[str],
        Field(
            description="Path to metadata storage",
        ),
    ] = None
    collection_id: Annotated[
        Optional[str], Field(description="A reference to a DLite collection.")
    ] = None

    url: Annotated[Optional[str], Field(description="url to the db")] = None

    USER: Annotated[Optional[str], Field(description="user to the db")] = None

    PASSWORD: Annotated[
        Optional[SecretStr], Field(description="user pwd to the db")
    ] = None

    DATABASE: Annotated[Optional[str], Field(description="database name")] = (
        None
    )

    RETPOLICY: Annotated[
        Optional[str], Field(description="retpolicy for db")
    ] = None

    time_range: Annotated[
        str, Field(description="timerange of values. eg : -12h")
    ] = "-12h"

    size_limit: Annotated[
        int, Field(description="rows to be extracted", ge=0)
    ] = 50

    measurements: Annotated[
        list[Measurement],
        Field(description="Measurement and field values as a list."),
    ] = [
        Measurement(**_)
        for _ in [
            {
                "measurement": "ctd_conductivity_munkholmen",
                "field": "conductivity",
            },
            {
                "measurement": "ctd_density_munkholmen",
                "field": "density",
            },
            {
                "measurement": "ctd_salinity_munkholmen",
                "field": "salinity",
            },
            {
                "measurement": "ctd_pressure_munkholmen",
                "field": "pressure",
            },
        ]
    ]


class InfluxParseStrategyConfig(ParserConfig):
    """DLite excel parse strategy  config."""

    configuration: Annotated[
        InfluxParseParseConfig,
        Field(
            description="DLite InfluxDB parse strategy-specific configuration."
        ),
    ]


class InfluxParserUpdate(DLiteSessionUpdate):
    """Class for returning values from DLite json parser."""

    inst_uuid: Annotated[
        str,
        Field(
            description="UUID of new instance.",
        ),
    ]
    label: Annotated[
        str,
        Field(
            description="Label of the new instance in the collection.",
        ),
    ]


@dataclass
class InfluxParseStrategy:
    """Parse strategy for Influx DB.

    **Registers strategies**:

    - `("parserType",
        "influx/vnd.dlite-influx")`

    """

    parse_config: InfluxParseStrategyConfig

    def initialize(self) -> DLiteSessionUpdate:
        """Initialize."""
        collection_id = (
            self.parse_config.configuration.collection_id
            or get_collection().uuid
        )
        return DLiteSessionUpdate(collection_id=collection_id)

    def get(self) -> InfluxParserUpdate:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint
        of the OTE-API Services.

        Returns:
            DLite instance.

        """
        config = self.parse_config.configuration
        try:
            # Update dlite storage paths if provided
            if config.storage_path:
                for storage_path in config.storage_path.split("|"):
                    dlite.storage_path.append(storage_path)
        except Exception as e:
            logger.error("Error during update of DLite storage path: %s", e)
            raise RuntimeError("Failed to update DLite storage path.") from e

        try:
            env = jinja2.Environment(loader=jinja2.BaseLoader, autoescape=True)
            env.globals.update(enumerate=enumerate, str=str)
            bucket = f"{config.DATABASE}/{config.RETPOLICY}"
            configuration = {
                "bucket": bucket,
                "timeRange": config.time_range,
                "limitSize": str(config.size_limit),
                "measurements": [
                    measurement.model_dump()
                    for measurement in config.measurements
                ],
            }
            tmpl = env.from_string(TEMPLATE)
            flux_query = tmpl.render(configuration).strip()
            columns = query_to_df(
                flux_query,
                config.url,
                config.USER,
                config.PASSWORD.get_secret_value(),  # type: ignore
            )
        except Exception as e:
            # Handle errors that occur during JSON parser instantiation or
            # data retrieval. You can log the exception, raise a custom
            # exception, or handle it as needed. For example, logging the
            # error and raising a custom exception:
            logger.error("Error during JSON parsing: %s", e)
            raise RuntimeError("Failed to parse JSON data.") from e

        # Create DLite instance
        meta = get_meta(self.parse_config.entity)
        inst = meta(dims=[configuration["limitSize"]])

        for name in [
            measurement["field"]  # type: ignore
            for measurement in configuration["measurements"]
        ]:
            inst[name] = columns[name]
        inst["time"] = [
            d.strftime("%m/%d/%Y, %H:%M:%S") for d in columns["_time"]
        ]
        # Add collection and add the entity instance
        coll = get_collection(
            collection_id=self.parse_config.configuration.collection_id
        )
        coll.add(config.label, inst)
        update_collection(coll)

        return InfluxParserUpdate(
            collection_id=coll.uuid,
            inst_uuid=inst.uuid,
            label=config.label,
        )


@cachetools.cached(cache=cachetools.LRUCache(maxsize=128))
def query_to_df(
    query: str, url: str, USER: str, PASSWORD: SecretStr
) -> DataFrame:
    """query_to_df"""
    with influxdb_client.InfluxDBClient(
        url=url, token=f"{USER}:{PASSWORD}"
    ) as client:
        return client.query_api().query_data_frame(query)


# Define the Jinja2 template :
# This creates the query to fetch data from the
# influxdb based on the measurement and DB field.
TEMPLATE = """{% macro fetchData(measurement, field) %}
    from(bucket: "{{ bucket }}")
      |> range(start: -1d)
      |> filter(fn: (r) => r._measurement == "{{ measurement }}")
      |> filter(fn: (r) => r._field == "{{ field }}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> limit(n: 50)
    {% endmacro %}

    {%- for index, measurement in enumerate(measurements, 1) %}
    data{{ index }} = {{ fetchData(measurement.measurement, measurement.field) }}
    {%- endfor %}

    {%- for index in range(1, measurements | length) %}
    join{{ index }} = join(
      tables: {
        left: {{ "data" + str(index) if index == 1 else "join" + str(index - 1) }},
        right: data{{ index + 1 }}
      },
      on: ["_time"]
    )
    {%- endfor %}

    finalData = join{{ measurements | length - 1 }}
      |> keep(columns: ["_time",
        {%- for measurement in measurements %}
        "{{ measurement.field }}"{% if not loop.last %}, {% endif %}
        {%- endfor %}
      ])

    finalData
"""
