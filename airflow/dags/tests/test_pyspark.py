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
   merge_and_transform(spark_session = pyspark_session, include_livingcost = False, items_to_filter_by =
   ['Price per Square Meter to Buy Apartment in City Centre', 'Price per Square Meter to Buy Apartment Outside of Centre'], output_file = 'homepurchase')
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

def test_merge_and_transform_foodbeverage(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform(spark_session = pyspark_session, include_livingcost = True, items_to_filter_by =
   ['Milk (1L)', 'Bread (500g)', 'Rice (1kg)', 'Eggs (x12)', 'Cheese (1kg)', 'Chicken Fillets (1kg)', 'Beef Round (1kg)', 'Apples (1kg)', 'Banana (1kg)',
   'Oranges (1kg)', 'Tomato (1kg)', 'Potato (1kg)', 'Onion (1kg)', 'Lettuce (1 Head)', 'Water (1L)', 'Wine (750ml Bottle Mid Range)',
   'Domestic Beer (0.5L Bottle)', 'Cigarettes (20 Pack Malboro)', 'Dinner (2 People Mid Range Restaurant)', 'Lunch', 'Domestic Draught (0.5L)',
   'Cappuccino (Regular)', 'Coke (0.5L)'], output_file = 'foodbeverage')
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}'),
   call(Bucket = 'test-bucket-raw', Key = f'livingcost_price_info{current_date}')]
   expected_foodbeverage = json.dumps([{"City": "Perth", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 96.31, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Domestic Draught (0.5L)", "Price": 7.41, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Cappuccino (Regular)", "Price": 3.64, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Perth", "Item": "Milk (1L)", "Price": 1.82, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
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
   {"City": "Auckland", "Item": "Domestic Draught (0.5L)", "Price": 7.0, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Cappuccino (Regular)", "Price": 3.56, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Milk (1L)", "Price": 1.97, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
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
   {"City": "Hong Kong", "Item": "Domestic Draught (0.5L)", "Price": 6.39, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Cappuccino (Regular)", "Price": 5.05, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Milk (1L)", "Price": 3.08, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
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
   {"City": "Asuncion", "Item": "Domestic Draught (0.5L)", "Price": 1.35, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Cappuccino (Regular)", "Price": 2.28, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Milk (1L)", "Price": 0.82, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
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
   {"City": "Perth", "Item": "Water (1L)", "Price": 1.43, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Perth", "Item": "Wine (750ml Bottle Mid Range)", "Price": 13.4, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Lunch", "Price": 12.9, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Coke (0.5L)", "Price": 2.55, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Auckland", "Item": "Water (1L)", "Price": 0.8, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Auckland", "Item": "Wine (750ml Bottle Mid Range)", "Price": 12.2, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Lunch", "Price": 7.33, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Coke (0.5L)", "Price": 1.17, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Hong Kong", "Item": "Water (1L)", "Price": 1.04, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Hong Kong", "Item": "Wine (750ml Bottle Mid Range)", "Price": 20.5, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Lunch", "Price": 4.13, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Coke (0.5L)", "Price": 1.03, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
   {"City": "Asuncion", "Item": "Water (1L)", "Price": 0.4, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
   {"City": "Asuncion", "Item": "Wine (750ml Bottle Mid Range)", "Price": 5.45, "Purchase Point": "Supermarket", "Item Category": "Beverage"}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'foodbeverage{current_date}',
   Body = expected_foodbeverage)

def test_merge_and_transform_utilities(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform(spark_session = pyspark_session, include_livingcost = True, 
   items_to_filter_by = ['Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Electricity, Heating, Cooling, Water and Garbage (Family)',
   'Internet (60 Mbps, Unlimited Data, Monthly)', 'Mobile Plan (10GB+ Data, Monthly)'], output_file = 'utilities')
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}'),
   call(Bucket = 'test-bucket-raw', Key = f'livingcost_price_info{current_date}')]
   expected_utilities = json.dumps([{"City": "Perth", "Item": "Mobile Plan (10GB+ Data, Monthly)", "Price": 35.83}, 
   {"City": "Perth", "Item": "Internet (60 Mbps, Unlimited Data, Monthly)", "Price": 62.23}, 
   {"City": "Auckland", "Item": "Mobile Plan (10GB+ Data, Monthly)", "Price": 40.35}, 
   {"City": "Auckland", "Item": "Internet (60 Mbps, Unlimited Data, Monthly)", "Price": 52.52},
   {"City": "Hong Kong", "Item": "Mobile Plan (10GB+ Data, Monthly)", "Price": 19.08}, 
   {"City": "Hong Kong", "Item": "Internet (60 Mbps, Unlimited Data, Monthly)", "Price": 23.51}, 
   {"City": "Asuncion", "Item": "Mobile Plan (10GB+ Data, Monthly)", "Price": 15.59}, 
   {"City": "Asuncion", "Item": "Internet (60 Mbps, Unlimited Data, Monthly)", "Price": 18.57}, 
   {"City": "Perth", "Item": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Price": 124.0}, 
   {"City": "Perth", "Item": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Price": 216.0}, 
   {"City": "Auckland", "Item": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Price": 96.1}, 
   {"City": "Auckland", "Item": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Price": 148.0}, 
   {"City": "Hong Kong", "Item": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Price": 146.0}, 
   {"City": "Hong Kong", "Item": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Price": 223.0}, 
   {"City": "Asuncion", "Item": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Price": 39.3}, 
   {"City": "Asuncion", "Item": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Price": 61.3}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'utilities{current_date}',
   Body = expected_utilities)

def test_merge_and_transform_rent(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform(spark_session = pyspark_session, include_livingcost = False, 
   items_to_filter_by = ['Rent 1 Bedroom Apartment City Centre', 'Rent 1 Bedroom Apartment Outside City Centre',
   'Rent 3 Bedroom Apartment City Centre', 'Rent 3 Bedroom Apartment Outside City Centre'], output_file = 'rent')
   expected_rent = json.dumps([{"City": "Perth", "Item": "Rent 1 Bedroom Apartment City Centre", "Price": 1635.10}, 
   {"City": "Perth", "Item": "Rent 1 Bedroom Apartment Outside City Centre", "Price": 1191.26}, 
   {"City": "Perth", "Item": "Rent 3 Bedroom Apartment City Centre", "Price": 2454.62}, 
   {"City": "Perth", "Item": "Rent 3 Bedroom Apartment Outside City Centre", "Price": 1763.16},
   {"City": "Auckland", "Item": "Rent 1 Bedroom Apartment City Centre", "Price": 1279.42}, 
   {"City": "Auckland", "Item": "Rent 1 Bedroom Apartment Outside City Centre", "Price": 1213.58}, 
   {"City": "Auckland", "Item": "Rent 3 Bedroom Apartment City Centre", "Price": 2417.70}, 
   {"City": "Auckland", "Item": "Rent 3 Bedroom Apartment Outside City Centre", "Price": 1926.70}, 
   {"City": "Hong Kong", "Item": "Rent 1 Bedroom Apartment City Centre", "Price": 2315.70}, 
   {"City": "Hong Kong", "Item": "Rent 1 Bedroom Apartment Outside City Centre", "Price": 1663.10}, 
   {"City": "Hong Kong", "Item": "Rent 3 Bedroom Apartment City Centre", "Price": 4608.27}, 
   {"City": "Hong Kong", "Item": "Rent 3 Bedroom Apartment Outside City Centre", "Price": 2953.79}, 
   {"City": "Asuncion", "Item": "Rent 1 Bedroom Apartment City Centre", "Price": 362.12}, 
   {"City": "Asuncion", "Item": "Rent 1 Bedroom Apartment Outside City Centre", "Price": 272.89}, 
   {"City": "Asuncion", "Item": "Rent 3 Bedroom Apartment City Centre", "Price": 685.78}, 
   {"City": "Asuncion", "Item": "Rent 3 Bedroom Apartment Outside City Centre", "Price": 610.63}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'rent{current_date}',
   Body = expected_rent)

def test_merge_and_transform_transportation(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform(spark_session = pyspark_session, include_livingcost = True, items_to_filter_by =
   ['Public Transport (One Way Ticket)', 'Public Transport (Monthly)', 'Petrol (1L)', 'Taxi (8km)'], output_file = 'transportation')
   expected_get_object_calls = [call(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}'),
   call(Bucket = 'test-bucket-raw', Key = f'livingcost_price_info{current_date}')]
   expected_transportation = json.dumps([{"City": "Perth", "Item": "Public Transport (One Way Ticket)", "Price": 2.90}, 
   {"City": "Perth", "Item": "Public Transport (Monthly)", "Price": 112.90}, 
   {"City": "Perth", "Item": "Petrol (1L)", "Price": 1.26}, 
   {"City": "Auckland", "Item": "Public Transport (One Way Ticket)", "Price": 2.33}, 
   {"City": "Auckland", "Item": "Public Transport (Monthly)", "Price": 125.43}, 
   {"City": "Auckland", "Item": "Petrol (1L)", "Price": 1.67}, 
   {"City": "Hong Kong", "Item": "Public Transport (One Way Ticket)", "Price": 1.53}, 
   {"City": "Hong Kong", "Item": "Public Transport (Monthly)", "Price": 63.90}, 
   {"City": "Hong Kong", "Item": "Petrol (1L)", "Price": 2.88}, 
   {"City": "Asuncion", "Item": "Public Transport (One Way Ticket)", "Price": 0.49}, 
   {"City": "Asuncion", "Item": "Public Transport (Monthly)", "Price": 21.57}, 
   {"City": "Asuncion", "Item": "Petrol (1L)", "Price": 1.12}, 
   {"City": "Perth", "Item": "Taxi (8km)", "Price": 17.4},
   {"City": "Auckland", "Item": "Taxi (8km)", "Price": 19.7}, 
   {"City": "Hong Kong", "Item": "Taxi (8km)", "Price": 13.0},
   {"City": "Asuncion", "Item": "Taxi (8km)", "Price": 9.43}])
   assert mock_boto3_s3.get_object.call_count == 2
   assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'transportation{current_date}',
   Body = expected_transportation)

def test_merge_and_transform_apparel(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform(spark_session = pyspark_session, include_livingcost = True, items_to_filter_by =
   ['Pair of Jeans', 'Summer Dress Chain Store', 'Mens Leather Business Shoes', 'Brand Sneakers'], output_file = 'apparel')
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
   Body = expected_apparel)

def test_merge_and_transform_apparel(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform(spark_session = pyspark_session, include_livingcost = True, items_to_filter_by =
   ['Pair of Jeans', 'Summer Dress Chain Store', 'Mens Leather Business Shoes', 'Brand Sneakers'], output_file = 'apparel')
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
   Body = expected_apparel)
   
def test_merge_and_transform_childcare(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform(spark_session = pyspark_session, include_livingcost = False, 
   items_to_filter_by = ['Daycare / Preschool (1 Month)', 'International Primary School (1 Year)'], output_file = 'childcare')
   expected_childcare = json.dumps([{"City": "Perth", "Item": "Daycare / Preschool (1 Month)", "Price": 1617.64}, 
   {"City": "Perth", "Item": "International Primary School (1 Year)", "Price": 13498.21}, 
   {"City": "Auckland", "Item": "Daycare / Preschool (1 Month)", "Price": 829.42}, 
   {"City": "Auckland", "Item": "International Primary School (1 Year)", "Price": 13521.14},
   {"City": "Hong Kong", "Item": "Daycare / Preschool (1 Month)", "Price": 783.72}, 
   {"City": "Hong Kong", "Item": "International Primary School (1 Year)", "Price": 20470.76}, 
   {"City": "Asuncion", "Item": "Daycare / Preschool (1 Month)", "Price": 165.08}, 
   {"City": "Asuncion", "Item": "International Primary School (1 Year)", "Price": 3436.45}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'childcare{current_date}',
   Body = expected_childcare)

def test_merge_and_transform_leisure(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, mocker):
   merge_and_transform(spark_session = pyspark_session, include_livingcost = False, 
   items_to_filter_by = ['Gym Membership (Monthly)', 'Tennis Court Rent (1hr)', 'Cinema International Release'], output_file = 'leisure')
   expected_leisure = json.dumps([{"City": "Perth", "Item": "Gym Membership (Monthly)", "Price": 49.05}, 
   {"City": "Perth", "Item": "Tennis Court Rent (1hr)", "Price": 14.92}, 
   {"City": "Perth", "Item": "Cinema International Release", "Price": 14.82}, 
   {"City": "Auckland", "Item": "Gym Membership (Monthly)", "Price": 45.83}, 
   {"City": "Auckland", "Item": "Tennis Court Rent (1hr)", "Price": 18.16}, 
   {"City": "Auckland", "Item": "Cinema International Release", "Price": 13.42}, 
   {"City": "Hong Kong", "Item": "Gym Membership (Monthly)", "Price": 88.44}, 
   {"City": "Hong Kong", "Item": "Tennis Court Rent (1hr)", "Price": 8.85}, 
   {"City": "Hong Kong", "Item": "Cinema International Release", "Price": 12.78},
   {"City": "Asuncion", "Item": "Gym Membership (Monthly)", "Price": 30.28}, 
   {"City": "Asuncion", "Item": "Tennis Court Rent (1hr)", "Price": 11.12}, 
   {"City": "Asuncion", "Item": "Cinema International Release", "Price": 6.06}])
   mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
   mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'leisure{current_date}',
   Body = expected_leisure)




