import pytest
import json
import boto3
import os
import datetime
from utils.aws_utils import get_data
from tests.fixtures.fixtures_testing import mock_environment_variables, mock_boto3_s3, pyspark_session

# Current date for asserts
current_date = datetime.date.today().strftime('%Y%m%d')

def test_merge_cities_and_currencies(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date):
   expected_cities_with_currencies = json.dumps([{'Country': 'Australia', 'City': 'Perth', 'Abbreviation': 'AUD', 'USD_to_local': 1.55}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'cities{current_date}')
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'currency_conversion_rates{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'cities_with_currencies{current_date}',
   Body = expected_cities_with_currencies)




