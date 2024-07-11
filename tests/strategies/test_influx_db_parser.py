"""Test Influx db parser"""

import unittest
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from oteapi_dlite.strategies.oceanlab_influx_parser import (
    InfluxParseParseConfig,
    InfluxParseStrategyConfig,
    query_to_df,
)


class TestInfluxParseParseConfig(unittest.TestCase):
    """Test configuration"""

    def test_valid_config(self):
        """Test configuration validity"""
        config = InfluxParseParseConfig(
            id="test_id",
            label="test_label",
            resourceType="resource/url",
            downloadUrl="http://example.com",
            mediaType="application/json",
            storage_path="/path/to/storage",
            collection_id="test_collection_id",
            url="http://db.url",
            USER="test_user",
            PASSWORD="test_password",
            DATABASE="test_db",
            RETPOLICY="test_policy",
        )
        assert config.id == "test_id"
        assert config.label == "test_label"

    def test_invalid_config(self):
        """Test validation error"""
        with self.assertRaises(ValidationError):
            InfluxParseParseConfig(id=123)  # id should be a string or None


class TestInfluxParseStrategyConfig(unittest.TestCase):
    """Test strategy config"""

    def test_valid_strategy_config(self):
        """Test config instance"""
        parse_config = InfluxParseParseConfig()
        strategy_config = InfluxParseStrategyConfig(
            parserType="influx/vnd.dlite-influx",
            entity="http://onto-ns.com/meta/oceanlab/1/ctd_salinity_munkholmen",
            configuration=parse_config,
        )
        assert isinstance(strategy_config.configuration, InfluxParseParseConfig)


class TestInfluxParseStrategy(unittest.TestCase):
    """Test functions in ParserStrategy"""

    @patch("influxdb_client.InfluxDBClient")
    def test_query_to_df(self, mock_influxdb_client):
        """Test query to df"""
        mock_client = MagicMock()
        mock_query_api = MagicMock()
        mock_client.query_api.return_value = mock_query_api
        mock_influxdb_client.return_value.__enter__.return_value = mock_client

        mock_df = MagicMock()
        mock_query_api.query_data_frame.return_value = mock_df

        result = query_to_df(
            "test_query", "http://db.url", "test_user", "test_password"
        )
        assert result == mock_df
        mock_influxdb_client.assert_called_once_with(
            url="http://db.url", token="test_user:test_password"
        )
