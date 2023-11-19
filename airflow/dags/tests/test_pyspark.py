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
   merge_locations_with_currencies(spark_session = pyspark_session)
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = 'locations.json'),
   call(Bucket = 'test-bucket-raw', Key = f'currency_conversion_rates{current_date}')]
   expected_locations_with_currencies = json.dumps([{"Abbreviation": "AUD", "Country": "Australia", "City": "Perth", "USD_to_local": 1.55},
   {"Abbreviation": "HKD", "Country": "Hong Kong", "City": "Hong Kong", "USD_to_local": 7.82},
   {"Abbreviation": "NZD", "Country": "New Zealand", "City": "Auckland", "USD_to_local": 1.69}, 
   {"Abbreviation": "PYG", "Country": "Paraguay", "City": "Asuncion", "USD_to_local": 7258.93}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'locations_with_currencies{current_date}',
   Body = expected_locations_with_currencies, ContentType = 'application/json')

def test_merge_and_transform_homepurchase(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_homepurchase(spark_session = pyspark_session)
   expected_homepurchase = json.dumps([{"City": "Asuncion", "Property Location": "Outside City Centre", "Price per Square Meter": 1118.53, "Mortgage Interest": 9.67}, 
   {"City": "Asuncion", "Property Location": "Outside City Centre", "Price per Square Meter": 933.23, "Mortgage Interest": 9.67}, 
   {"City": "Auckland", "Property Location": "City Centre", "Price per Square Meter": 9155.42, "Mortgage Interest": 6.81}, 
   {"City": "Auckland", "Property Location": "Outside City Centre", "Price per Square Meter": 8089.96, "Mortgage Interest": 6.81}, 
   {"City": "Hong Kong", "Property Location": "City Centre", "Price per Square Meter": 30603.04, "Mortgage Interest": 3.22}, 
   {"City": "Hong Kong", "Property Location": "Outside City Centre", "Price per Square Meter": 20253.04, "Mortgage Interest": 3.22}, 
   {"City": "Perth", "Property Location": "City Centre", "Price per Square Meter": 6741.52, "Mortgage Interest": 5.99}, 
   {"City": "Perth", "Property Location": "Outside City Centre", "Price per Square Meter": 5395.77, "Mortgage Interest": 5.99}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'homepurchase{current_date}',
   Body = expected_homepurchase, ContentType = 'application/json')

def test_merge_and_transform_rent(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_rent(spark_session = pyspark_session)
   expected_rent = json.dumps([{"City": "Perth", "Monthly Price": 1635.1, "Property Location": "City Centre", "Bedrooms": 1}, 
   {"City": "Perth", "Monthly Price": 1191.26, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
   {"City": "Perth", "Monthly Price": 2454.62, "Property Location": "City Centre", "Bedrooms": 3}, 
   {"City": "Perth", "Monthly Price": 1763.16, "Property Location": "Outside City Centre", "Bedrooms": 3}, 
   {"City": "Auckland", "Monthly Price": 1279.42, "Property Location": "City Centre", "Bedrooms": 1}, 
   {"City": "Auckland", "Monthly Price": 1213.58, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
   {"City": "Auckland", "Monthly Price": 2417.7, "Property Location": "City Centre", "Bedrooms": 3}, 
   {"City": "Auckland", "Monthly Price": 1926.7, "Property Location": "Outside City Centre", "Bedrooms": 3}, 
   {"City": "Hong Kong", "Monthly Price": 2315.7, "Property Location": "City Centre", "Bedrooms": 1}, 
   {"City": "Hong Kong", "Monthly Price": 1663.1, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
   {"City": "Hong Kong", "Monthly Price": 4608.27, "Property Location": "City Centre", "Bedrooms": 3}, 
   {"City": "Hong Kong", "Monthly Price": 2953.79, "Property Location": "Outside City Centre", "Bedrooms": 3}, 
   {"City": "Asuncion", "Monthly Price": 362.12, "Property Location": "City Centre", "Bedrooms": 1}, 
   {"City": "Asuncion", "Monthly Price": 272.89, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
   {"City": "Asuncion", "Monthly Price": 685.78, "Property Location": "City Centre", "Bedrooms": 3}, 
   {"City": "Asuncion", "Monthly Price": 610.63, "Property Location": "Outside City Centre", "Bedrooms": 3}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'rent{current_date}',
   Body = expected_rent, ContentType = 'application/json')

def test_merge_and_transform_foodbeverage(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_foodbeverage(spark_session = pyspark_session)
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}'),
   call(Bucket = 'test-bucket-raw', Key = f'livingcost_price_info{current_date}')]
   expected_foodbeverage = json.dumps([{"City": "Perth", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 96.31, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Domestic Draught (0.5L)", "Price": 7.41, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Perth", "Item": "Cappuccino (Regular)", "Price": 3.64, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Perth", "Item": "Milk (1L)", "Price": 1.82, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Perth", "Item": "Bread (500g)", "Price": 2.44, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Rice (1kg)", "Price": 2.19, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Eggs (x12)", "Price": 4.22, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Cheese (1kg)", "Price": 9.47, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Chicken Fillets (1kg)", "Price": 8.85, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Beef Round (1kg)", "Price": 14.47, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Apples (1kg)", "Price": 3.44, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Banana (1kg)", "Price": 2.58, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Oranges (1kg)", "Price": 2.93, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Tomato (1kg)", "Price": 4.27, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Potato (1kg)", "Price": 2.19, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Onion (1kg)", "Price": 1.76, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Lettuce (1 Head)", "Price": 2.27, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Domestic Beer (0.5L Bottle)", "Price": 4.62, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 70.01, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Domestic Draught (0.5L)", "Price": 7.0, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Cappuccino (Regular)", "Price": 3.56, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Milk (1L)", "Price": 1.97, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Bread (500g)", "Price": 2.13, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Rice (1kg)", "Price": 2.09, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Eggs (x12)", "Price": 6.43, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Cheese (1kg)", "Price": 8.87, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Chicken Fillets (1kg)", "Price": 9.99, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Beef Round (1kg)", "Price": 13.28, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Apples (1kg)", "Price": 2.79, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Banana (1kg)", "Price": 2.27, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Oranges (1kg)", "Price": 3.02, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Tomato (1kg)", "Price": 6.29, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Potato (1kg)", "Price": 2.48, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Onion (1kg)", "Price": 2.06, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Lettuce (1 Head)", "Price": 2.85, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Domestic Beer (0.5L Bottle)", "Price": 3.67, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 63.9, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Domestic Draught (0.5L)", "Price": 6.39, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Cappuccino (Regular)", "Price": 5.05, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Milk (1L)", "Price": 3.08, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Bread (500g)", "Price": 2.26, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Rice (1kg)", "Price": 2.52, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Eggs (x12)", "Price": 3.86, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Cheese (1kg)", "Price": 24.67, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Chicken Fillets (1kg)", "Price": 9.56, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Beef Round (1kg)", "Price": 25.24, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Apples (1kg)", "Price": 4.24, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Banana (1kg)", "Price": 2.52, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Oranges (1kg)", "Price": 4.16, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Tomato (1kg)", "Price": 3.1, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Potato (1kg)", "Price": 2.71, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Onion (1kg)", "Price": 2.68, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Lettuce (1 Head)", "Price": 1.47, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Domestic Beer (0.5L Bottle)", "Price": 1.88, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 22.91, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Domestic Draught (0.5L)", "Price": 1.35, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Cappuccino (Regular)", "Price": 2.28, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Milk (1L)", "Price": 0.82, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Bread (500g)", "Price": 0.73, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Rice (1kg)", "Price": 0.91, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Eggs (x12)", "Price": 2.16, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Cheese (1kg)", "Price": 6.43, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Chicken Fillets (1kg)", "Price": 4.16, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Beef Round (1kg)", "Price": 6.37, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Apples (1kg)", "Price": 2.06, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Banana (1kg)", "Price": 0.94, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Oranges (1kg)", "Price": 0.98, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Tomato (1kg)", "Price": 1.5, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Potato (1kg)", "Price": 0.83, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Onion (1kg)", "Price": 0.71, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Lettuce (1 Head)", "Price": 0.47, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Domestic Beer (0.5L Bottle)", "Price": 1.07, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Perth", "Item": "Lunch", "Price": 15.4, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Coke (0.5L)", "Price": 2.95, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Perth", "Item": "Water (1L)", "Price": 1.43, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Perth", "Item": "Wine (750ml Bottle Mid Range)", "Price": 13.4, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Lunch", "Price": 12.9, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Coke (0.5L)", "Price": 2.55, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Water (1L)", "Price": 0.8, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Wine (750ml Bottle Mid Range)", "Price": 12.2, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Lunch", "Price": 7.33, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Coke (0.5L)", "Price": 1.17, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Water (1L)", "Price": 1.04, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Wine (750ml Bottle Mid Range)", "Price": 20.5, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Lunch", "Price": 4.13, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Coke (0.5L)", "Price": 1.03, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Water (1L)", "Price": 0.4, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Wine (750ml Bottle Mid Range)", "Price": 5.45, "Purchase Point": "Supermarket", "Item Category": "Beverage"}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'foodbeverage{current_date}',
   Body = expected_foodbeverage, ContentType = 'application/json')

def test_merge_and_transform_utilities(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_utilities(spark_session = pyspark_session)
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}'),
   call(Bucket = 'test-bucket-raw', Key = f'livingcost_price_info{current_date}')]
   expected_utilities = json.dumps([{"City": "Perth", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 35.83}, 
   {"City": "Perth", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 62.23}, 
   {"City": "Auckland", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 40.35}, 
   {"City": "Auckland", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 52.52},
   {"City": "Hong Kong", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 19.08}, 
   {"City": "Hong Kong", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 23.51}, 
   {"City": "Asuncion", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 15.59}, 
   {"City": "Asuncion", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 18.57}, 
   {"City": "Perth", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 124.0}, 
   {"City": "Perth", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 216.0}, 
   {"City": "Auckland", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 96.1}, 
   {"City": "Auckland", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 148.0}, 
   {"City": "Hong Kong", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 146.0}, 
   {"City": "Hong Kong", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 223.0}, 
   {"City": "Asuncion", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 39.3}, 
   {"City": "Asuncion", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 61.3}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'utilities{current_date}',
   Body = expected_utilities, ContentType = 'application/json')

def test_merge_and_transform_transportation(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_transportation(spark_session = pyspark_session)
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}'),
   call(Bucket = 'test-bucket-raw', Key = f'livingcost_price_info{current_date}')]
   expected_transportation = json.dumps([{"City": "Perth", "Type": "Public Transport (One Way Ticket)", "Price": 2.90}, 
   {"City": "Perth", "Type": "Public Transport (Monthly)", "Price": 112.90}, 
   {"City": "Perth", "Type": "Petrol (1L)", "Price": 1.26}, 
   {"City": "Auckland", "Type": "Public Transport (One Way Ticket)", "Price": 2.33}, 
   {"City": "Auckland", "Type": "Public Transport (Monthly)", "Price": 125.43}, 
   {"City": "Auckland", "Type": "Petrol (1L)", "Price": 1.67}, 
   {"City": "Hong Kong", "Type": "Public Transport (One Way Ticket)", "Price": 1.53}, 
   {"City": "Hong Kong", "Type": "Public Transport (Monthly)", "Price": 63.90}, 
   {"City": "Hong Kong", "Type": "Petrol (1L)", "Price": 2.88}, 
   {"City": "Asuncion", "Type": "Public Transport (One Way Ticket)", "Price": 0.49}, 
   {"City": "Asuncion", "Type": "Public Transport (Monthly)", "Price": 21.57}, 
   {"City": "Asuncion", "Type": "Petrol (1L)", "Price": 1.12}, 
   {"City": "Perth", "Type": "Taxi (8km)", "Price": 17.4},
   {"City": "Auckland", "Type": "Taxi (8km)", "Price": 19.7}, 
   {"City": "Hong Kong", "Type": "Taxi (8km)", "Price": 13.0},
   {"City": "Asuncion", "Type": "Taxi (8km)", "Price": 9.43}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'transportation{current_date}',
   Body = expected_transportation, ContentType = 'application/json')

def test_merge_and_transform_childcare(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_childcare(spark_session = pyspark_session)
   expected_childcare = json.dumps([{"City": "Perth", "Type": "Daycare / Preschool", "Annual Price": 19411.68}, 
   {"City": "Perth", "Type": "International Primary School", "Annual Price": 13498.21}, 
   {"City": "Auckland", "Type": "Daycare / Preschool", "Annual Price": 9953.04}, 
   {"City": "Auckland", "Type": "International Primary School", "Annual Price": 13521.14},
   {"City": "Hong Kong", "Type": "Daycare / Preschool", "Annual Price": 9404.64}, 
   {"City": "Hong Kong", "Type": "International Primary School", "Annual Price": 20470.76}, 
   {"City": "Asuncion", "Type": "Daycare / Preschool", "Annual Price": 1980.96}, 
   {"City": "Asuncion", "Type": "International Primary School", "Annual Price": 3436.45}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'childcare{current_date}',
   Body = expected_childcare, ContentType = 'application/json')

def test_merge_and_transform_apparel(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_apparel(spark_session = pyspark_session)
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}'),
   call(Bucket = 'test-bucket-raw', Key = f'livingcost_price_info{current_date}')]
   expected_apparel = json.dumps([{"City": "Perth", "Item": "Pair of Jeans", "Price": 87.19}, 
   {"City": "Perth", "Item": "Summer Dress Chain Store", "Price": 62.76}, 
   {"City": "Perth", "Item": "Mens Leather Business Shoes", "Price": 161.79}, 
   {"City": "Auckland", "Item": "Pair of Jeans", "Price": 82.11}, 
   {"City": "Auckland", "Item": "Summer Dress Chain Store", "Price": 52.16}, 
   {"City": "Auckland", "Item": "Mens Leather Business Shoes", "Price": 122.07}, 
   {"City": "Hong Kong", "Item": "Pair of Jeans", "Price": 81.83}, 
   {"City": "Hong Kong", "Item": "Summer Dress Chain Store", "Price": 41.51}, 
   {"City": "Hong Kong", "Item": "Mens Leather Business Shoes", "Price": 127.96}, 
   {"City": "Asuncion", "Item": "Pair of Jeans", "Price": 39.76}, 
   {"City": "Asuncion", "Item": "Summer Dress Chain Store", "Price": 26.62}, 
   {"City": "Asuncion", "Item": "Mens Leather Business Shoes", "Price": 69.63}, 
   {"City": "Perth", "Item": "Brand Sneakers", "Price": 139.0}, 
   {"City": "Auckland", "Item": "Brand Sneakers", "Price": 103.0}, 
   {"City": "Hong Kong", "Item": "Brand Sneakers", "Price": 86.5}, 
   {"City": "Asuncion", "Item": "Brand Sneakers", "Price": 85.6}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'apparel{current_date}',
   Body = expected_apparel, ContentType = 'application/json')

def test_merge_and_transform_leisure(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform_leisure(spark_session = pyspark_session)
   expected_leisure = json.dumps([{"City": "Perth", "Activity": "Gym Membership (Monthly)", "Price": 49.05}, 
   {"City": "Perth", "Activity": "Tennis Court Rent (1hr)", "Price": 14.92}, 
   {"City": "Perth", "Activity": "Cinema International Release", "Price": 14.82}, 
   {"City": "Auckland", "Activity": "Gym Membership (Monthly)", "Price": 45.83}, 
   {"City": "Auckland", "Activity": "Tennis Court Rent (1hr)", "Price": 18.16}, 
   {"City": "Auckland", "Activity": "Cinema International Release", "Price": 13.42}, 
   {"City": "Hong Kong", "Activity": "Gym Membership (Monthly)", "Price": 88.44}, 
   {"City": "Hong Kong", "Activity": "Tennis Court Rent (1hr)", "Price": 8.85}, 
   {"City": "Hong Kong", "Activity": "Cinema International Release", "Price": 12.78},
   {"City": "Asuncion", "Activity": "Gym Membership (Monthly)", "Price": 30.28}, 
   {"City": "Asuncion", "Activity": "Tennis Court Rent (1hr)", "Price": 11.12}, 
   {"City": "Asuncion", "Activity": "Cinema International Release", "Price": 6.06}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'leisure{current_date}',
   Body = expected_leisure, ContentType = 'application/json')




