import pytest
import time
import os
import requests_mock
import boto3
import datetime
from flask import json, url_for
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Mock email and password for testing purposes
TEST_EMAIL = 'test@gmail.com'
TEST_PASSWORD = 'X4nmasXII!'

@pytest.fixture
def create_user(client):
    new_user = client.post('/v1/auth/user',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return new_user

@pytest.fixture
def login(client, create_user):
    login = client.post('/v1/auth/login',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD
        }))
    login_data = json.loads(login.get_data(as_text = True))
    return login_data

def create_currency(client, abbreviation, usd_to_local_exchange_rate):
        response = client.post('/v1/currencies',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'abbreviation': abbreviation,
            'usd_to_local_exchange_rate': usd_to_local_exchange_rate,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        return response

def create_location(client, country, city, abbreviation):
    response = client.post('/v1/locations',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'country': country,
        'city': city,
        'abbreviation': abbreviation,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_home_purchase(client,property_location,price_per_sqm,mortgage_interest,city):
    response = client.post('/v1/homepurchase',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': property_location,
        'price_per_sqm': price_per_sqm,
        'mortgage_interest': mortgage_interest,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_rent(client,property_location,bedrooms,monthly_price,city):
    response = client.post('/v1/rent',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': property_location,
        'bedrooms': bedrooms,
        'monthly_price': monthly_price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_utilities(client,utility,monthly_price,city):
    response = client.post('/v1/utilities',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'utility': utility,
        'monthly_price': monthly_price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_transportation(client,type,price,city):
    response = client.post('/v1/transportation',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': type,
        'price': price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_foodbeverage(client,item_category,purchase_point,item,price,city):
    response = client.post('/v1/foodbeverage',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item_category': item_category,
        'purchase_point': purchase_point,
        'item': item,
        'price': price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_childcare(client,type,annual_price,city):
    response = client.post('/v1/childcare',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': type,
        'annual_price': annual_price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_apparel(client,item,price,city):
    response = client.post('/v1/apparel',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item': item,
        'price': price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

def create_leisure(client,activity,price,city):
    response = client.post('/v1/leisure',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'activity': activity,
        'price': price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

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
    {"City": "Asuncion", "Property Location": "City Centre", "Price per Square Meter": 1118.53, "Mortgage Interest": 9.67}, 
    {"City": "Asuncion", "Property Location": "Outside of Centre", "Price per Square Meter": 933.23, "Mortgage Interest": 9.67}, 
    {"City": "Auckland", "Property Location": "City Centre", "Price per Square Meter": 9155.42, "Mortgage Interest": 6.81}, 
    {"City": "Auckland", "Property Location": "Outside of Centre", "Price per Square Meter": 8089.96, "Mortgage Interest": 6.81}, 
    {"City": "Hong Kong", "Property Location": "City Centre", "Price per Square Meter": 30603.04, "Mortgage Interest": 3.22}, 
    {"City": "Hong Kong", "Property Location": "Outside of Centre", "Price per Square Meter": 20253.04, "Mortgage Interest": 3.22}, 
    {"City": "Perth", "Property Location": "City Centre", "Price per Square Meter": 6741.52, "Mortgage Interest": 5.99}, 
    {"City": "Perth", "Property Location": "Outside of Centre", "Price per Square Meter": 5395.77, "Mortgage Interest": 5.99}]).encode('utf-8')))},
    f'rent{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Monthly Price": 1635.1, "Property Location": "City Centre", "Bedrooms": 1}, 
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
    {"City": "Asuncion", "Monthly Price": 610.63, "Property Location": "Outside City Centre", "Bedrooms": 3}]).encode('utf-8')))},
    f'foodbeverage{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps(
    [{"City": "Perth", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 96.31, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
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
    {"City": "Asuncion", "Item": "Wine (750ml Bottle Mid Range)", "Price": 5.45, "Purchase Point": "Supermarket", "Item Category": "Beverage"}]).encode('utf-8')))},
    f'utilities{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 35.83}, 
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
    {"City": "Asuncion", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 61.3}]).encode('utf-8')))},
    f'transportation{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Type": "Public Transport (One Way Ticket)", "Price": 2.90}, 
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
    {"City": "Asuncion", "Type": "Taxi (8km)", "Price": 9.43}]).encode('utf-8')))},
    f'childcare{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Type": "Daycare / Preschool (1 Month)", "Annual Price": 1617.64}, 
    {"City": "Perth", "Type": "International Primary School (1 Year)", "Annual Price": 13498.21}, 
    {"City": "Auckland", "Type": "Daycare / Preschool (1 Month)", "Annual Price": 829.42}, 
    {"City": "Auckland", "Type": "International Primary School (1 Year)", "Annual Price": 13521.14},
    {"City": "Hong Kong", "Type": "Daycare / Preschool (1 Month)", "Annual Price": 783.72}, 
    {"City": "Hong Kong", "Type": "International Primary School (1 Year)", "Annual Price": 20470.76}, 
    {"City": "Asuncion", "Type": "Daycare / Preschool (1 Month)", "Annual Price": 165.08}, 
    {"City": "Asuncion", "Type": "International Primary School (1 Year)", "Annual Price": 3436.45}]).encode('utf-8')))},
    f'apparel{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Item": "Pair of Jeans", "Price": 87.19}, 
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
    {"City": "Asuncion", "Item": "Brand Sneakers", "Price": 85.6}]).encode('utf-8')))},
    f'leisure{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Activity": "Gym Membership (Monthly)", "Price": 49.05}, 
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
    {"City": "Asuncion", "Activity": "Cinema International Release", "Price": 6.06}]).encode('utf-8')))}
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
    {"City": "Asuncion", "Property Location": "City Centre", "Price per Square Meter": 1118.53, "Mortgage Interest": 9.67}, 
    {"City": "Asuncion", "Property Location": "Outside of Centre", "Price per Square Meter": 933.23, "Mortgage Interest": 9.67}, 
    {"City": "Auckland", "Property Location": "City Centre", "Price per Square Meter": 9155.42, "Mortgage Interest": 6.81}, 
    {"City": "Auckland", "Property Location": "Outside of Centre", "Price per Square Meter": 8089.96, "Mortgage Interest": 6.81}, 
    {"City": "Hong Kong", "Property Location": "City Centre", "Price per Square Meter": 30603.04, "Mortgage Interest": 3.22}, 
    {"City": "Hong Kong", "Property Location": "Outside of Centre", "Price per Square Meter": 20253.04, "Mortgage Interest": 3.22}, 
    {"City": "Perth", "Property Location": "City Centre", "Price per Square Meter": 7120.84, "Mortgage Interest": 5.99}, 
    {"City": "Perth", "Property Location": "Outside of Centre", "Price per Square Meter": 5824.95, "Mortgage Interest": 5.99}]).encode('utf-8')))},
    f'rent{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Monthly Price": 1756.41, "Property Location": "City Centre", "Bedrooms": 1}, 
    {"City": "Perth", "Monthly Price": 1285.83, "Property Location": "Outside City Centre", "Bedrooms": 1}, 
    {"City": "Perth", "Monthly Price": 2588.74, "Property Location": "City Centre", "Bedrooms": 3}, 
    {"City": "Perth", "Monthly Price": 1885.67, "Property Location": "Outside City Centre", "Bedrooms": 3}, 
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
    {"City": "Asuncion", "Monthly Price": 610.63, "Property Location": "Outside City Centre", "Bedrooms": 3}]).encode('utf-8')))},
    f'foodbeverage{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps(
    [{"City": "Perth", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": 97.68, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Domestic Draught (0.5L)", "Price": 7.81, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Cappuccino (Regular)", "Price": 3.80, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Perth", "Item": "Milk (1L)", "Price": 1.96, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Bread (500g)", "Price": 2.54, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Rice (1kg)", "Price": 2.48, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Eggs (x12)", "Price": 4.45, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Cheese (1kg)", "Price": 9.60, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Chicken Fillets (1kg)", "Price": 9.14, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Beef Round (1kg)", "Price": 15.00, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Apples (1kg)", "Price": 3.58, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Banana (1kg)", "Price": 2.74, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Oranges (1kg)", "Price": 3.06, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Tomato (1kg)", "Price": 4.27, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Potato (1kg)", "Price": 2.47, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Onion (1kg)", "Price": 1.80, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Lettuce (1 Head)", "Price": 2.34, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Domestic Beer (0.5L Bottle)", "Price": 4.60, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
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
    {"City": "Perth", "Item": "Lunch", "Price": 15.41, "Purchase Point": "Restaurant", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Coke (0.5L)", "Price": 2.96, "Purchase Point": "Restaurant", "Item Category": "Beverage"}, 
    {"City": "Perth", "Item": "Water (1L)", "Price": 1.44, "Purchase Point": "Supermarket", "Item Category": "Food"}, 
    {"City": "Perth", "Item": "Wine (750ml Bottle Mid Range)", "Price": 13.41, "Purchase Point": "Supermarket", "Item Category": "Beverage"}, 
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
    {"City": "Asuncion", "Item": "Wine (750ml Bottle Mid Range)", "Price": 5.45, "Purchase Point": "Supermarket", "Item Category": "Beverage"}]).encode('utf-8')))},
    f'utilities{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 36.14}, 
    {"City": "Perth", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 62.97}, 
    {"City": "Auckland", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 40.35}, 
    {"City": "Auckland", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 52.52},
    {"City": "Hong Kong", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 19.08}, 
    {"City": "Hong Kong", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 23.51}, 
    {"City": "Asuncion", "Utility": "Mobile Plan (10GB+ Data, Monthly)", "Monthly Price": 15.59}, 
    {"City": "Asuncion", "Utility": "Internet (60 Mbps, Unlimited Data, Monthly)", "Monthly Price": 18.57}, 
    {"City": "Perth", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 125.0}, 
    {"City": "Perth", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 217.0}, 
    {"City": "Auckland", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 96.1}, 
    {"City": "Auckland", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 148.0}, 
    {"City": "Hong Kong", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 146.0}, 
    {"City": "Hong Kong", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 223.0}, 
    {"City": "Asuncion", "Utility": "Electricity, Heating, Cooling, Water and Garbage (1 Person)", "Monthly Price": 39.3}, 
    {"City": "Asuncion", "Utility": "Electricity, Heating, Cooling, Water and Garbage (Family)", "Monthly Price": 61.3}]).encode('utf-8')))},
    f'transportation{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Type": "Public Transport (One Way Ticket)", "Price": 2.94}, 
    {"City": "Perth", "Type": "Public Transport (Monthly)", "Price": 114.13}, 
    {"City": "Perth", "Type": "Petrol (1L)", "Price": 1.30}, 
    {"City": "Auckland", "Type": "Public Transport (One Way Ticket)", "Price": 2.33}, 
    {"City": "Auckland", "Type": "Public Transport (Monthly)", "Price": 125.43}, 
    {"City": "Auckland", "Type": "Petrol (1L)", "Price": 1.67}, 
    {"City": "Hong Kong", "Type": "Public Transport (One Way Ticket)", "Price": 1.53}, 
    {"City": "Hong Kong", "Type": "Public Transport (Monthly)", "Price": 63.90}, 
    {"City": "Hong Kong", "Type": "Petrol (1L)", "Price": 2.88}, 
    {"City": "Asuncion", "Type": "Public Transport (One Way Ticket)", "Price": 0.49}, 
    {"City": "Asuncion", "Type": "Public Transport (Monthly)", "Price": 21.57}, 
    {"City": "Asuncion", "Type": "Petrol (1L)", "Price": 1.12}, 
    {"City": "Perth", "Type": "Taxi (8km)", "Price": 17.41},
    {"City": "Auckland", "Type": "Taxi (8km)", "Price": 19.7}, 
    {"City": "Hong Kong", "Type": "Taxi (8km)", "Price": 13.0},
    {"City": "Asuncion", "Type": "Taxi (8km)", "Price": 9.43}]).encode('utf-8')))},
    f'childcare{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Type": "Daycare / Preschool (1 Month)", "Annual Price": 1716.59}, 
    {"City": "Perth", "Type": "International Primary School (1 Year)", "Annual Price": 13837.01}, 
    {"City": "Auckland", "Type": "Daycare / Preschool (1 Month)", "Annual Price": 829.42}, 
    {"City": "Auckland", "Type": "International Primary School (1 Year)", "Annual Price": 13521.14},
    {"City": "Hong Kong", "Type": "Daycare / Preschool (1 Month)", "Annual Price": 783.72}, 
    {"City": "Hong Kong", "Type": "International Primary School (1 Year)", "Annual Price": 20470.76}, 
    {"City": "Asuncion", "Type": "Daycare / Preschool (1 Month)", "Annual Price": 165.08}, 
    {"City": "Asuncion", "Type": "International Primary School (1 Year)", "Annual Price": 3436.45}]).encode('utf-8')))},
    f'apparel{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Item": "Pair of Jeans", "Price": 90.22}, 
    {"City": "Perth", "Item": "Summer Dress Chain Store", "Price": 74.84}, 
    {"City": "Perth", "Item": "Mens Leather Business Shoes", "Price": 171.78}, 
    {"City": "Auckland", "Item": "Pair of Jeans", "Price": 82.11}, 
    {"City": "Auckland", "Item": "Summer Dress Chain Store", "Price": 52.16}, 
    {"City": "Auckland", "Item": "Mens Leather Business Shoes", "Price": 122.07}, 
    {"City": "Hong Kong", "Item": "Pair of Jeans", "Price": 81.83}, 
    {"City": "Hong Kong", "Item": "Summer Dress Chain Store", "Price": 41.51}, 
    {"City": "Hong Kong", "Item": "Mens Leather Business Shoes", "Price": 127.96}, 
    {"City": "Asuncion", "Item": "Pair of Jeans", "Price": 39.76}, 
    {"City": "Asuncion", "Item": "Summer Dress Chain Store", "Price": 26.62}, 
    {"City": "Asuncion", "Item": "Mens Leather Business Shoes", "Price": 69.63}, 
    {"City": "Perth", "Item": "Brand Sneakers", "Price": 139.1}, 
    {"City": "Auckland", "Item": "Brand Sneakers", "Price": 103.0}, 
    {"City": "Hong Kong", "Item": "Brand Sneakers", "Price": 86.5}, 
    {"City": "Asuncion", "Item": "Brand Sneakers", "Price": 85.6}]).encode('utf-8')))},
    f'leisure{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([
    {"City": "Perth", "Activity": "Gym Membership (Monthly)", "Price": 49.56}, 
    {"City": "Perth", "Activity": "Tennis Court Rent (1hr)", "Price": 15.25}, 
    {"City": "Perth", "Activity": "Cinema International Release", "Price": 15.30}, 
    {"City": "Auckland", "Activity": "Gym Membership (Monthly)", "Price": 45.83}, 
    {"City": "Auckland", "Activity": "Tennis Court Rent (1hr)", "Price": 18.16}, 
    {"City": "Auckland", "Activity": "Cinema International Release", "Price": 13.42}, 
    {"City": "Hong Kong", "Activity": "Gym Membership (Monthly)", "Price": 88.44}, 
    {"City": "Hong Kong", "Activity": "Tennis Court Rent (1hr)", "Price": 8.85}, 
    {"City": "Hong Kong", "Activity": "Cinema International Release", "Price": 12.78},
    {"City": "Asuncion", "Activity": "Gym Membership (Monthly)", "Price": 30.28}, 
    {"City": "Asuncion", "Activity": "Tennis Court Rent (1hr)", "Price": 11.12}, 
    {"City": "Asuncion", "Activity": "Cinema International Release", "Price": 6.06}]).encode('utf-8')))}
    }
    def mock_get_object(Bucket, Key, **kwargs):
        # Extract the prefix from the Key
        file_prefix = Key[:]

        # Return the corresponding value from return_values
        return return_values.get(file_prefix, {})

    mock_s3.get_object.side_effect = mock_get_object
    return mock_s3