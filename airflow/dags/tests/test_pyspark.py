import pytest
import json
import boto3
import os
import datetime
from unittest.mock import call
from utils.aws_utils import get_data
from tests.fixtures.fixtures_testing import mock_environment_variables, mock_boto3_s3, pyspark_session, current_date
from scripts.pyspark import *

def test_merge_cities_and_currencies(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_cities_with_currencies(spark_session = pyspark_session, country_abbreviation_combinations = country_abbreviation_combinations)
   expected_get_object_calls = [call(Bucket='test-bucket-raw', Key=f'cities{current_date}'),
   call(Bucket='test-bucket-raw', Key=f'currency_conversion_rates{current_date}')]
   expected_cities_with_currencies = json.dumps([{"Abbreviation": "AUD", "Country": "Australia", "City": "Perth", "USD_to_local": 1.55},
   {"Abbreviation": "NZD", "Country": "New Zealand", "City": "Auckland", "USD_to_local": 1.69}, 
   {"Abbreviation": "PYG", "Country": "Paraguay", "City": "Asuncion", "USD_to_local": 7258.93}, 
   {"Abbreviation": "SGD", "Country": "Singapore", "City": "Singapore", "USD_to_local": 1.36}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'cities_with_currencies{current_date}',
   Body = expected_cities_with_currencies)




