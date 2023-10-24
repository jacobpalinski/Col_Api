import pytest
import json
import boto3
import os
import datetime
from unittest.mock import call
from utils.aws_utils import get_data
from tests.fixtures.fixtures_testing import mock_environment_variables, mock_boto3_s3, pyspark_session, current_date
from scripts.pyspark import *

def test_merge_locations_and_currencies(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_locations_with_currencies(spark_session = pyspark_session, country_abbreviation_combinations = country_abbreviation_combinations)
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = 'locations.json'),
   call(Bucket = 'test-bucket-raw', Key = f'currency_conversion_rates{current_date}')]
   expected_locations_with_currencies = json.dumps([{"Abbreviation": "AUD", "Country": "Australia", "City": "Perth", "USD_to_local": 1.55},
   {"Abbreviation": "HKD", "Country": "Hong Kong", "City": "Hong Kong", "USD_to_local": 7.82},
   {"Abbreviation": "NZD", "Country": "New Zealand", "City": "Auckland", "USD_to_local": 1.69}, 
   {"Abbreviation": "PYG", "Country": "Paraguay", "City": "Asuncion", "USD_to_local": 7258.93}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'locations_with_currencies{current_date}',
   Body = expected_locations_with_currencies)

def test_merge_and_transform_homepurchase(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_homepurchase(spark_session = pyspark_session)
   expected_homepurchase = json.dumps([{"City": "Perth", "Item": "Price per Square Meter to Buy Apartment in City Centre", "Price": 6741.52},
   {"City": "Perth", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": 5395.77},
   {"City": "Auckland", "Item": "Price per Square Meter to Buy Apartment in City Centre", "Price": 9155.42},
   {"City": "Auckland", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": 8089.96},
   {"City": "Hong Kong", "Item": "Price per Square Meter to Buy Apartment in City Centre", "Price": 30603.04},
   {"City": "Hong Kong", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": 20253.04},
   {"City": "Asuncion", "Item": "Price per Square Meter to Buy Apartment in City Centre", "Price": 1118.53},
   {"City": "Asuncion", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": 933.23}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'homepurchase{current_date}',
   Body = expected_homepurchase)




