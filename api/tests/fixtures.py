import pytest
import time
import os
import requests_mock
import boto3
import datetime
from flask import json, url_for
from dotenv import load_dotenv

# Mock environment variables
@pytest.fixture
def mock_environment_variables(mocker):
    mocker.patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'access-key',
    'AWS_SECRET_ACCESS_KEY': 'secret-key',
    'S3_BUCKET_RAW': 'test-bucket-raw',
    'S3_BUCKET_TRANSFORMED': 'test-bucket-transformed',
    'ADMIN_KEY' : 'admin-key'
    })

# Mock email and password for testing purposes
TEST_EMAIL = 'test@gmail.com'
TEST_PASSWORD = 'X4nmasXII!'

@pytest.fixture
def current_date():
    return datetime.date.today().strftime('%Y%m%d')

@pytest.fixture
def mock_boto3_s3(mocker, monkeypatch, current_date):
    mock_s3 = mocker.Mock()
    monkeypatch.setattr(boto3, 'client', lambda *args, **kwargs: mock_s3)

    return_values = {
    f'locations_with_currencies{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps([
    {"Abbreviation": "AUD", "Country": "Australia", "City": "Perth", "USD_to_local": 1.55},
    {"Abbreviation": "HKD", "Country": "Hong Kong", "City": "Hong Kong", "USD_to_local": 7.82},
    {"Abbreviation": "NZD", "Country": "New Zealand", "City": "Auckland", "USD_to_local": 1.69}, 
    {"Abbreviation": "PYG", "Country": "Paraguay", "City": "Asuncion", "USD_to_local": 7258.93}]).encode('utf-8')))},
    f'homepurchase{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps([ 
    {"City": "Hong Kong", "Property Location": "City Centre", "Price per Square Meter": 30603.04, "Mortgage Interest": 3.22}, 
    {"City": "Hong Kong", "Property Location": "Outside City Centre", "Price per Square Meter": 20253.04, "Mortgage Interest": 3.22},
    {"City": "Perth", "Property Location": "City Centre", "Price per Square Meter": 6741.52, "Mortgage Interest": 5.99}, 
    {"City": "Perth", "Property Location": "Outside City Centre", "Price per Square Meter": 5395.77, "Mortgage Interest": 5.99}]).encode('utf-8')))},
    f'rent{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Monthly Price": 1635.1, "Property Location": "City Centre", "Bedrooms": 1}, 
    {"City": "Perth", "Monthly Price": 1191.26, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
    {"City": "Perth", "Monthly Price": 2454.62, "Property Location": "City Centre", "Bedrooms": 3}, 
    {"City": "Perth", "Monthly Price": 1763.16, "Property Location": "Outside City Centre", "Bedrooms": 3}, 
    {"City": "Hong Kong", "Monthly Price": 2315.7, "Property Location": "City Centre", "Bedrooms": 1}, 
    {"City": "Hong Kong", "Monthly Price": 1663.1, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
    {"City": "Hong Kong", "Monthly Price": 4608.27, "Property Location": "City Centre", "Bedrooms": 3}, 
    {"City": "Hong Kong", "Monthly Price": 2953.79, "Property Location": "Outside City Centre", "Bedrooms": 3}, ]).encode('utf-8')))},
    f'foodbeverage{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps(
    [{"City": "Perth", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 96.31, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Domestic Draught (0.5L)", "Price": 7.41, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Perth", "Item": "Cappuccino (Regular)", "Price": 3.64, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Perth", "Item": "Milk (1L)", "Price": 1.82, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
    {"City": "Perth", "Item": "Bread (500g)", "Price": 2.44, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Hong Kong", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 63.9, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
    {"City": "Hong Kong", "Item": "Domestic Draught (0.5L)", "Price": 6.39, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Hong Kong", "Item": "Cappuccino (Regular)", "Price": 5.05, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Hong Kong", "Item": "Milk (1L)", "Price": 3.08, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
    {"City": "Hong Kong", "Item": "Bread (500g)", "Price": 2.26, "Purchase Point": "Supermarket", "Item Category": "Food"}]).encode('utf-8')))},
    f'utilities{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 35.83}, 
    {"City": "Perth", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 62.23},
    {"City": "Hong Kong", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 19.08}, 
    {"City": "Hong Kong", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 23.51}, 
    {"City": "Perth", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 124.0}, 
    {"City": "Perth", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 216.0},  
    {"City": "Hong Kong", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 146.0}, 
    {"City": "Hong Kong", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 223.0}]).encode('utf-8')))},
    f'transportation{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Type": "Public Transport (One Way Ticket)", "Price": 2.90}, 
    {"City": "Perth", "Type": "Public Transport (Monthly)", "Price": 112.90}, 
    {"City": "Perth", "Type": "Petrol (1L)", "Price": 1.26},  
    {"City": "Hong Kong", "Type": "Public Transport (One Way Ticket)", "Price": 1.53}, 
    {"City": "Hong Kong", "Type": "Public Transport (Monthly)", "Price": 63.90}, 
    {"City": "Hong Kong", "Type": "Petrol (1L)", "Price": 2.88}, 
    {"City": "Perth", "Type": "Taxi (8km)", "Price": 17.4}, 
    {"City": "Hong Kong", "Type": "Taxi (8km)", "Price": 13.0}]).encode('utf-8')))},
    f'childcare{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Type": "Daycare / Preschool", "Annual Price": 19411.68}, 
    {"City": "Perth", "Type": "International Primary School", "Annual Price": 13498.21},
    {"City": "Hong Kong", "Type": "Daycare / Preschool", "Annual Price": 9404.64}, 
    {"City": "Hong Kong", "Type": "International Primary School", "Annual Price": 20470.76}]).encode('utf-8')))},
    f'apparel{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Item": "Pair of Jeans", "Price": 87.19}, 
    {"City": "Perth", "Item": "Summer Dress Chain Store", "Price": 62.76}, 
    {"City": "Perth", "Item": "Mens Leather Business Shoes", "Price": 161.79}, 
    {"City": "Hong Kong", "Item": "Pair of Jeans", "Price": 81.83}, 
    {"City": "Hong Kong", "Item": "Summer Dress Chain Store", "Price": 41.51}, 
    {"City": "Hong Kong", "Item": "Mens Leather Business Shoes", "Price": 127.96}, 
    {"City": "Perth", "Item": "Brand Sneakers", "Price": 139.0}, 
    {"City": "Hong Kong", "Item": "Brand Sneakers", "Price": 86.5}]).encode('utf-8')))},
    f'leisure{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Activity": "Gym Membership (Monthly)", "Price": 49.05}, 
    {"City": "Perth", "Activity": "Tennis Court Rent (1hr)", "Price": 14.92}, 
    {"City": "Perth", "Activity": "Cinema International Release", "Price": 14.82}, 
    {"City": "Hong Kong", "Activity": "Gym Membership (Monthly)", "Price": 88.44}, 
    {"City": "Hong Kong", "Activity": "Tennis Court Rent (1hr)", "Price": 8.85}, 
    {"City": "Hong Kong", "Activity": "Cinema International Release", "Price": 12.78}]).encode('utf-8')))}
    }
    def mock_get_object(Bucket, Key, **kwargs):
        # Extract the prefix from the Key
        file_prefix = Key[:]

        # Return the corresponding value from return_values
        return return_values.get(file_prefix, {})

    mock_s3.get_object.side_effect = mock_get_object
    return mock_s3

@pytest.fixture
def mock_boto3_s3_patch_modified(mocker, monkeypatch, current_date):
    mock_s3 = mocker.Mock()
    monkeypatch.setattr(boto3, 'client', lambda *args, **kwargs: mock_s3)

    return_values = {
    f'locations_with_currencies{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps([
    {"Abbreviation": "AUD", "Country": "Australia", "City": "Perth", "USD_to_local": 1.54},
    {"Abbreviation": "HKD", "Country": "Hong Kong", "City": "Hong Kong", "USD_to_local": 7.82},
    {"Abbreviation": "NZD", "Country": "New Zealand", "City": "Auckland", "USD_to_local": 1.69}, 
    {"Abbreviation": "PYG", "Country": "Paraguay", "City": "Asuncion", "USD_to_local": 7258.93}]).encode('utf-8')))},
    f'homepurchase{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps([ 
    {"City": "Hong Kong", "Property Location": "City Centre", "Price per Square Meter": 30603.04, "Mortgage Interest": 3.22}, 
    {"City": "Hong Kong", "Property Location": "Outside City Centre", "Price per Square Meter": 20253.04, "Mortgage Interest": 3.22}, 
    {"City": "Perth", "Property Location": "City Centre", "Price per Square Meter": 7120.84, "Mortgage Interest": 5.99}, 
    {"City": "Perth", "Property Location": "Outside City Centre", "Price per Square Meter": 5824.95, "Mortgage Interest": 5.99}]).encode('utf-8')))},
    f'rent{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Monthly Price": 1756.41, "Property Location": "City Centre", "Bedrooms": 1}, 
    {"City": "Perth", "Monthly Price": 1285.83, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
    {"City": "Perth", "Monthly Price": 2588.74, "Property Location": "City Centre", "Bedrooms": 3}, 
    {"City": "Perth", "Monthly Price": 1885.67, "Property Location": "Outside City Centre", "Bedrooms": 3}, 
    {"City": "Hong Kong", "Monthly Price": 2315.7, "Property Location": "City Centre", "Bedrooms": 1}, 
    {"City": "Hong Kong", "Monthly Price": 1663.1, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
    {"City": "Hong Kong", "Monthly Price": 4608.27, "Property Location": "City Centre", "Bedrooms": 3}, 
    {"City": "Hong Kong", "Monthly Price": 2953.79, "Property Location": "Outside City Centre", "Bedrooms": 3}]).encode('utf-8')))},
    f'foodbeverage{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps(
    [{"City": "Perth", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 97.68, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Domestic Draught (0.5L)", "Price": 7.81, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Perth", "Item": "Cappuccino (Regular)", "Price": 3.80, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Perth", "Item": "Milk (1L)", "Price": 1.96, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
    {"City": "Perth", "Item": "Bread (500g)", "Price": 2.54, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Hong Kong", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 63.9, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
    {"City": "Hong Kong", "Item": "Domestic Draught (0.5L)", "Price": 6.39, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Hong Kong", "Item": "Cappuccino (Regular)", "Price": 5.05, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Hong Kong", "Item": "Milk (1L)", "Price": 3.08, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
    {"City": "Hong Kong", "Item": "Bread (500g)", "Price": 2.26, "Purchase Point": "Supermarket", "Item Category": "Food"}]).encode('utf-8')))},
    f'utilities{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 36.14}, 
    {"City": "Perth", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 62.97},
    {"City": "Hong Kong", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 19.08}, 
    {"City": "Hong Kong", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 23.51}, 
    {"City": "Perth", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 125.0}, 
    {"City": "Perth", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 217.0}, 
    {"City": "Hong Kong", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 146.0}, 
    {"City": "Hong Kong", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 223.0}]).encode('utf-8')))},
    f'transportation{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Type": "Public Transport (One Way Ticket)", "Price": 2.94}, 
    {"City": "Perth", "Type": "Public Transport (Monthly)", "Price": 114.13}, 
    {"City": "Perth", "Type": "Petrol (1L)", "Price": 1.30}, 
    {"City": "Hong Kong", "Type": "Public Transport (One Way Ticket)", "Price": 1.53}, 
    {"City": "Hong Kong", "Type": "Public Transport (Monthly)", "Price": 63.90}, 
    {"City": "Hong Kong", "Type": "Petrol (1L)", "Price": 2.88}, 
    {"City": "Perth", "Type": "Taxi (8km)", "Price": 17.41}, 
    {"City": "Hong Kong", "Type": "Taxi (8km)", "Price": 13.0}]).encode('utf-8')))},
    f'childcare{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Type": "Daycare / Preschool", "Annual Price": 20599.08}, 
    {"City": "Perth", "Type": "International Primary School", "Annual Price": 13837.01},
    {"City": "Hong Kong", "Type": "Daycare / Preschool", "Annual Price": 9404.64}, 
    {"City": "Hong Kong", "Type": "International Primary School", "Annual Price": 20470.76}]).encode('utf-8')))},
    f'apparel{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Item": "Pair of Jeans", "Price": 90.22}, 
    {"City": "Perth", "Item": "Summer Dress Chain Store", "Price": 74.84}, 
    {"City": "Perth", "Item": "Mens Leather Business Shoes", "Price": 171.78}, 
    {"City": "Hong Kong", "Item": "Pair of Jeans", "Price": 81.83}, 
    {"City": "Hong Kong", "Item": "Summer Dress Chain Store", "Price": 41.51}, 
    {"City": "Hong Kong", "Item": "Mens Leather Business Shoes", "Price": 127.96}, 
    {"City": "Perth", "Item": "Brand Sneakers", "Price": 139.1}, 
    {"City": "Hong Kong", "Item": "Brand Sneakers", "Price": 86.5}]).encode('utf-8')))},
    f'leisure{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Activity": "Gym Membership (Monthly)", "Price": 49.56}, 
    {"City": "Perth", "Activity": "Tennis Court Rent (1hr)", "Price": 15.25}, 
    {"City": "Perth", "Activity": "Cinema International Release", "Price": 15.30}, 
    {"City": "Hong Kong", "Activity": "Gym Membership (Monthly)", "Price": 88.44}, 
    {"City": "Hong Kong", "Activity": "Tennis Court Rent (1hr)", "Price": 8.85}, 
    {"City": "Hong Kong", "Activity": "Cinema International Release", "Price": 12.78}]).encode('utf-8')))}
    }
    def mock_get_object(Bucket, Key, **kwargs):
        # Extract the prefix from the Key
        file_prefix = Key[:]

        # Return the corresponding value from return_values
        return return_values.get(file_prefix, {})

    mock_s3.get_object.side_effect = mock_get_object
    return mock_s3

@pytest.fixture
def create_user(client, mock_environment_variables):
    new_user = client.post('/v1/auth/user',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return new_user

@pytest.fixture
def login(client, create_user, mock_environment_variables):
    login = client.post('/v1/auth/login',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD
        }))
    login_data = json.loads(login.get_data(as_text = True))
    return login_data

def create_currency(client, mock_environment_variables):
    response = client.post('/v1/currencies',
    headers = {'Content-Type': 'application/json'},
    data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}
    ))
    return response

def currency_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/currencies',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_location(client, mock_environment_variables):
    response = client.post('/v1/locations',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_homepurchase(client, mock_environment_variables):
    response = client.post('/v1/homepurchase',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def homepurchase_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/homepurchase',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_rent(client, mock_environment_variables):
    response = client.post('/v1/rent',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def rent_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/rent',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_utilities(client, mock_environment_variables):
    response = client.post('/v1/utilities',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def utilities_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/utilities',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_transportation(client, mock_environment_variables):
    response = client.post('/v1/transportation',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def transportation_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/transportation',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_foodbeverage(client, mock_environment_variables):
    response = client.post('/v1/foodbeverage',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def foodbeverage_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/foodbeverage',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_childcare(client, mock_environment_variables):
    response = client.post('/v1/childcare',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def childcare_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/childcare',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_apparel(client, mock_environment_variables):
    response = client.post('/v1/apparel',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def apparel_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/apparel',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_leisure(client, mock_environment_variables):
    response = client.post('/v1/leisure',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def leisure_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified):
    response = client.patch('/v1/leisure',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response