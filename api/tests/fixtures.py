import pytest
import time
import os
import requests_mock
import boto3
from flask import json, url_for
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

@ pytest.fixture
def mock_boto3_s3(mocker, monkeypatch, current_date):
    mock_s3 = mocker.Mock()
    monkeypatch.setattr(boto3, 'client', lambda *args, **kwargs: mock_s3)

    return_values = {
        f'locations_with_currencies{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps([{'Country': 'Australia', 'City': 'Perth'},
        {'Country': 'New Zealand', 'City': 'Auckland'}, {'Country': 'Hong Kong', 'City': 'Hong Kong'}, {'Country': 'Paraguay', 'City': 'Asuncion'}]).encode('utf-8')))},
        f'currency_conversion_rates{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps([{'Abbreviation': 'AUD', 'USD_to_local': '1.55'},
        {'Abbreviation': 'NZD', 'USD_to_local': '1.69'}, {'Abbreviation': 'HKD', 'USD_to_local': '7.82'}, {'Abbreviation': 'PYG', 'USD_to_local': '7,258.93'}]).encode('utf-8')))},
        f'livingcost_price_info{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value = json.dumps([{'City': 'Perth', 'Item': 'Lunch', 'Price': '$15.4'},
        {'City': 'Perth', 'Item': 'Coke (0.5L)', 'Price': '$2.95'},
        {'City': 'Perth', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Price': '$124' },
        {'City': 'Perth', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (Family)', 'Price': '$216'},
        {'City': 'Perth', 'Item': 'Taxi (8km)', 'Price': '$17.4'},
        {'City': 'Perth', 'Item': 'Water (1L)', 'Price': '$1.43'},
        {'City': 'Perth', 'Item': 'Wine (750ml Bottle Mid Range)', 'Price': '$13.4'},
        {'City': 'Perth', 'Item': 'Brand Sneakers', 'Price': '$139'},
        {'City': 'Auckland', 'Item': 'Lunch', 'Price': '$12.9'},
        {'City': 'Auckland', 'Item': 'Coke (0.5L)', 'Price': '$2.55'},
        {'City': 'Auckland', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Price': '$96.1' },
        {'City': 'Auckland', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (Family)', 'Price': '$148'},
        {'City': 'Auckland', 'Item': 'Taxi (8km)', 'Price': '$19.7'},
        {'City': 'Auckland', 'Item': 'Water (1L)', 'Price': '$0.8'},
        {'City': 'Auckland', 'Item': 'Wine (750ml Bottle Mid Range)', 'Price': '$12.2'},
        {'City': 'Auckland', 'Item': 'Brand Sneakers', 'Price': '$103'},
        {'City': 'Hong Kong', 'Item': 'Lunch', 'Price': '$7.33'},
        {'City': 'Hong Kong', 'Item': 'Coke (0.5L)', 'Price': '$1.17'},
        {'City': 'Hong Kong', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Price': '$146' },
        {'City': 'Hong Kong', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (Family)', 'Price': '$223'},
        {'City': 'Hong Kong', 'Item': 'Taxi (8km)', 'Price': '$13'},
        {'City': 'Hong Kong', 'Item': 'Water (1L)', 'Price': '$1.04'},
        {'City': 'Hong Kong', 'Item': 'Wine (750ml Bottle Mid Range)', 'Price': '$20.5'},
        {'City': 'Hong Kong', 'Item': 'Brand Sneakers', 'Price': '$86.5'},
        {'City': 'Asuncion', 'Item': 'Lunch', 'Price': '$4.13'},
        {'City': 'Asuncion', 'Item': 'Coke (0.5L)', 'Price': '$1.03'},
        {'City': 'Asuncion', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Price': '$39.3' },
        {'City': 'Asuncion', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (Family)', 'Price': '$61.3'},
        {'City': 'Asuncion', 'Item': 'Taxi (8km)', 'Price': '$9.43'},
        {'City': 'Asuncion', 'Item': 'Water (1L)', 'Price': '$0.4'},
        {'City': 'Asuncion', 'Item': 'Wine (750ml Bottle Mid Range)', 'Price': '$5.45'},
        {'City': 'Asuncion', 'Item': 'Brand Sneakers', 'Price': '$85.6'}]).encode('utf-8')))},
        f'numbeo_price_info{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps(
        [{"City": "Perth", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": "96.31\u00a0$"},
        {"City": "Perth", "Item": "Domestic Draught (0.5L)", "Price": "7.41\u00a0$"},
        {"City": "Perth", "Item": "Cappuccino (Regular)", "Price": "3.64\u00a0$"},
        {"City": "Perth", "Item": "Milk (1L)", "Price": "1.82\u00a0$"},
        {"City": "Perth", "Item": "Bread (500g)", "Price": "2.44\u00a0$"},
        {"City": "Perth", "Item": "Rice (1kg)", "Price": "2.19\u00a0$"},
        {"City": "Perth", "Item": "Eggs (x12)", "Price": "4.22\u00a0$"},
        {"City": "Perth", "Item": "Cheese (1kg)", "Price": "9.47\u00a0$"},
        {"City": "Perth", "Item": "Chicken Fillets (1kg)", "Price": "8.85\u00a0$"},
        {"City": "Perth", "Item": "Beef Round (1kg)", "Price": "14.47\u00a0$"},
        {"City": "Perth", "Item": "Apples (1kg)", "Price": "3.44\u00a0$"},
        {"City": "Perth", "Item": "Banana (1kg)", "Price": "2.58\u00a0$"},
        {"City": "Perth", "Item": "Oranges (1kg)", "Price": "2.93\u00a0$"},
        {"City": "Perth", "Item": "Tomato (1kg)", "Price": "4.27\u00a0$"},
        {"City": "Perth", "Item": "Potato (1kg)", "Price": "2.19\u00a0$"},
        {"City": "Perth", "Item": "Onion (1kg)", "Price": "1.76\u00a0$"},
        {"City": "Perth", "Item": "Lettuce (1 Head)", "Price": "2.27\u00a0$"},
        {"City": "Perth", "Item": "Domestic Beer (0.5L Bottle)", "Price": "4.62\u00a0$"},
        {"City": "Perth", "Item": "Public Transport (One Way Ticket)", "Price": "2.90\u00a0$"},
        {"City": "Perth", "Item": "Public Transport (Monthly)", "Price": "112.90\u00a0$"},
        {"City": "Perth", "Item": "Petrol (1L)", "Price": "1.26\u00a0$"},
        {"City": "Perth", "Item": "Mobile Plan (10GB+ Data, Monthly)", "Price": "35.83\u00a0$"},
        {"City": "Perth", "Item": "Internet (60 Mbps, Unlimited Data, Monthly)", "Price": "62.23\u00a0$"},
        {"City": "Perth", "Item": "Gym Membership (Monthly)", "Price": "49.05\u00a0$"},
        {"City": "Perth", "Item": "Tennis Court Rent (1hr)", "Price": "14.92\u00a0$"},
        {"City": "Perth", "Item": "Cinema International Release", "Price": "14.82\u00a0$"},
        {"City": "Perth", "Item": "Daycare / Preschool (1 Month)", "Price": "1,617.64\u00a0$"},
        {"City": "Perth", "Item": "International Primary School (1 Year)", "Price": "13,498.21\u00a0$"},
        {"City": "Perth", "Item": "Pair of Jeans", "Price": "87.19\u00a0$"},
        {"City": "Perth", "Item": "Summer Dress Chain Store", "Price": "62.76\u00a0$"},
        {"City": "Perth", "Item": "Mens Leather Business Shoes", "Price": "161.79\u00a0$"},
        {"City": "Perth", "Item": "Rent 1 Bedroom Apartment City Centre", "Price": "1,635.10\u00a0$"},
        {"City": "Perth", "Item": "Rent 1 Bedroom Apartment Outside City Centre", "Price": "1,191.26\u00a0$"},
        {"City": "Perth", "Item": "Rent 3 Bedroom Apartment City Centre", "Price": "2,454.62\u00a0$"},
        {"City": "Perth", "Item": "Rent 3 Bedroom Apartment Outside City Centre", "Price": "1,763.16\u00a0$"},
        {"City": "Perth", "Item": "Price per Square Meter to Buy Apartment in City Centre", "Price": "6,741.52\u00a0$"},
        {"City": "Perth", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": "5,395.77\u00a0$"},
        {'City': "Perth", 'Item': 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)', 'Price': "5.99"},
        {"City": "Auckland", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": "70.01\u00a0$"},
        {"City": "Auckland", "Item": "Domestic Draught (0.5L)", "Price": "7.00\u00a0$"},
        {"City": "Auckland", "Item": "Cappuccino (Regular)", "Price": "3.56\u00a0$"},
        {"City": "Auckland", "Item": "Milk (1L)", "Price": "1.97\u00a0$"},
        {"City": "Auckland", "Item": "Bread (500g)", "Price": "2.13\u00a0$"},
        {"City": "Auckland", "Item": "Rice (1kg)", "Price": "2.09\u00a0$"},
        {"City": "Auckland", "Item": "Eggs (x12)", "Price": "6.43\u00a0$"},
        {"City": "Auckland", "Item": "Cheese (1kg)", "Price": "8.87\u00a0$"},
        {"City": "Auckland", "Item": "Chicken Fillets (1kg)", "Price": "9.99\u00a0$"},
        {"City": "Auckland", "Item": "Beef Round (1kg)", "Price": "13.28\u00a0$"},
        {"City": "Auckland", "Item": "Apples (1kg)", "Price": "2.79\u00a0$"},
        {"City": "Auckland", "Item": "Banana (1kg)", "Price": "2.27\u00a0$"},
        {"City": "Auckland", "Item": "Oranges (1kg)", "Price": "3.02\u00a0$"},
        {"City": "Auckland", "Item": "Tomato (1kg)", "Price": "6.29\u00a0$"},
        {"City": "Auckland", "Item": "Potato (1kg)", "Price": "2.48\u00a0$"},
        {"City": "Auckland", "Item": "Onion (1kg)", "Price": "2.06\u00a0$"},
        {"City": "Auckland", "Item": "Lettuce (1 Head)", "Price": "2.85\u00a0$"},
        {"City": "Auckland", "Item": "Domestic Beer (0.5L Bottle)", "Price": "3.67\u00a0$"},
        {"City": "Auckland", "Item": "Public Transport (One Way Ticket)", "Price": "2.33\u00a0$"},
        {"City": "Auckland", "Item": "Public Transport (Monthly)", "Price": "125.43\u00a0$"},
        {"City": "Auckland", "Item": "Petrol (1L)", "Price": "1.67\u00a0$"},
        {"City": "Auckland", "Item": "Mobile Plan (10GB+ Data, Monthly)", "Price": "40.35\u00a0$"},
        {"City": "Auckland", "Item": "Internet (60 Mbps, Unlimited Data, Monthly)", "Price": "52.52\u00a0$"},
        {"City": "Auckland", "Item": "Gym Membership (Monthly)", "Price": "45.83\u00a0$"},
        {"City": "Auckland", "Item": "Tennis Court Rent (1hr)", "Price": "18.16\u00a0$"},
        {"City": "Auckland", "Item": "Cinema International Release", "Price": "13.42\u00a0$"},
        {"City": "Auckland", "Item": "Daycare / Preschool (1 Month)", "Price": "829.42\u00a0$"},
        {"City": "Auckland", "Item": "International Primary School (1 Year)", "Price": "13,521.14\u00a0$"},
        {"City": "Auckland", "Item": "Pair of Jeans", "Price": "82.11\u00a0$"},
        {"City": "Auckland", "Item": "Summer Dress Chain Store", "Price": "52.16\u00a0$"},
        {"City": "Auckland", "Item": "Mens Leather Business Shoes", "Price": "122.07\u00a0$"},
        {"City": "Auckland", "Item": "Rent 1 Bedroom Apartment City Centre", "Price": "1,279.42\u00a0$"},
        {"City": "Auckland", "Item": "Rent 1 Bedroom Apartment Outside City Centre", "Price": "1,213.58\u00a0$"},
        {"City": "Auckland", "Item": "Rent 3 Bedroom Apartment City Centre", "Price": "2,417.70\u00a0$"},
        {"City": "Auckland", "Item": "Rent 3 Bedroom Apartment Outside City Centre", "Price": "1,926.70\u00a0$"},
        {"City": "Auckland", "Item": "Price per Square Meter to Buy Apartment in City Centre", "Price": "9,155.42\u00a0$"},
        {"City": "Auckland", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": "8,089.96\u00a0$"},
        {'City': "Auckland", 'Item': 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)', 'Price': "6.81"},
        {"City": "Hong Kong", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": "63.90\u00a0$"},
        {"City": "Hong Kong", "Item": "Domestic Draught (0.5L)", "Price": "6.39\u00a0$"},
        {"City": "Hong Kong", "Item": "Cappuccino (Regular)", "Price": "5.05\u00a0$"},
        {"City": "Hong Kong", "Item": "Milk (1L)", "Price": "3.08\u00a0$"},
        {"City": "Hong Kong", "Item": "Bread (500g)", "Price": "2.26\u00a0$"},
        {"City": "Hong Kong", "Item": "Rice (1kg)", "Price": "2.52\u00a0$"},
        {"City": "Hong Kong", "Item": "Eggs (x12)", "Price": "3.86\u00a0$"},
        {"City": "Hong Kong", "Item": "Cheese (1kg)", "Price": "24.67\u00a0$"},
        {"City": "Hong Kong", "Item": "Chicken Fillets (1kg)", "Price": "9.56\u00a0$"},
        {"City": "Hong Kong", "Item": "Beef Round (1kg)", "Price": "25.24\u00a0$"},
        {"City": "Hong Kong", "Item": "Apples (1kg)", "Price": "4.24\u00a0$"},
        {"City": "Hong Kong", "Item": "Banana (1kg)", "Price": "2.52\u00a0$"},
        {"City": "Hong Kong", "Item": "Oranges (1kg)", "Price": "4.16\u00a0$"},
        {"City": "Hong Kong", "Item": "Tomato (1kg)", "Price": "3.10\u00a0$"},
        {"City": "Hong Kong", "Item": "Potato (1kg)", "Price": "2.71\u00a0$"},
        {"City": "Hong Kong", "Item": "Onion (1kg)", "Price": "2.68\u00a0$"},
        {"City": "Hong Kong", "Item": "Lettuce (1 Head)", "Price": "1.47\u00a0$"},
        {"City": "Hong Kong", "Item": "Domestic Beer (0.5L Bottle)", "Price": "1.88\u00a0$"},
        {"City": "Hong Kong", "Item": "Public Transport (One Way Ticket)", "Price": "1.53\u00a0$"},
        {"City": "Hong Kong", "Item": "Public Transport (Monthly)", "Price": "63.90\u00a0$"},
        {"City": "Hong Kong", "Item": "Petrol (1L)", "Price": "2.88\u00a0$"},
        {"City": "Hong Kong", "Item": "Mobile Plan (10GB+ Data, Monthly)", "Price": "19.08\u00a0$"},
        {"City": "Hong Kong", "Item": "Internet (60 Mbps, Unlimited Data, Monthly)", "Price": "23.51\u00a0$"},
        {"City": "Hong Kong", "Item": "Gym Membership (Monthly)", "Price": "88.44\u00a0$"},
        {"City": "Hong Kong", "Item": "Tennis Court Rent (1hr)", "Price": "8.85\u00a0$"},
        {"City": "Hong Kong", "Item": "Cinema International Release", "Price": "12.78\u00a0$"},
        {"City": "Hong Kong", "Item": "Daycare / Preschool (1 Month)", "Price": "783.72\u00a0$"},
        {"City": "Hong Kong", "Item": "International Primary School (1 Year)", "Price": "20,470.76\u00a0$"},
        {"City": "Hong Kong", "Item": "Pair of Jeans", "Price": "81.83\u00a0$"},
        {"City": "Hong Kong", "Item": "Summer Dress Chain Store", "Price": "41.51\u00a0$"},
        {"City": "Hong Kong", "Item": "Mens Leather Business Shoes", "Price": "127.96\u00a0$"},
        {"City": "Hong Kong", "Item": "Rent 1 Bedroom Apartment City Centre", "Price": "2,315.70\u00a0$"},
        {"City": "Hong Kong", "Item": "Rent 1 Bedroom Apartment Outside City Centre", "Price": "1,663.10\u00a0$"},
        {"City": "Hong Kong", "Item": "Rent 3 Bedroom Apartment City Centre", "Price": "4,608.27\u00a0$"},
        {"City": "Hong Kong", "Item": "Rent 3 Bedroom Apartment Outside City Centre", "Price": "2,953.79\u00a0$"},
        {"City": "Hong Kong", "Item": "Price per Square Meter to Buy Apartment in City Centre", "Price": "30,603.04\u00a0$"},
        {"City": "Hong Kong", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": "20,253.04\u00a0$"},
        {'City': "Hong Kong", 'Item': 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)', 'Price': "3.22"},
        {"City": "Asuncion", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": "22.91\u00a0$"},
        {"City": "Asuncion", "Item": "Domestic Draught (0.5L)", "Price": "1.35\u00a0$"},
        {"City": "Asuncion", "Item": "Cappuccino (Regular)", "Price": "2.28\u00a0$"},
        {"City": "Asuncion", "Item": "Milk (1L)", "Price": "0.82\u00a0$"},
        {"City": "Asuncion", "Item": "Bread (500g)", "Price": "0.73\u00a0$"},
        {"City": "Asuncion", "Item": "Rice (1kg)", "Price": "0.91\u00a0$"},
        {"City": "Asuncion", "Item": "Eggs (x12)", "Price": "2.16\u00a0$"},
        {"City": "Asuncion", "Item": "Cheese (1kg)", "Price": "6.43\u00a0$"},
        {"City": "Asuncion", "Item": "Chicken Fillets (1kg)", "Price": "4.16\u00a0$"},
        {"City": "Asuncion", "Item": "Beef Round (1kg)", "Price": "6.37\u00a0$"},
        {"City": "Asuncion", "Item": "Apples (1kg)", "Price": "2.06\u00a0$"},
        {"City": "Asuncion", "Item": "Banana (1kg)", "Price": "0.94\u00a0$"},
        {"City": "Asuncion", "Item": "Oranges (1kg)", "Price": "0.98\u00a0$"},
        {"City": "Asuncion", "Item": "Tomato (1kg)", "Price": "1.50\u00a0$"},
        {"City": "Asuncion", "Item": "Potato (1kg)", "Price": "0.83\u00a0$"},
        {"City": "Asuncion", "Item": "Onion (1kg)", "Price": "0.71\u00a0$"},
        {"City": "Asuncion", "Item": "Lettuce (1 Head)", "Price": "0.47\u00a0$"},
        {"City": "Asuncion", "Item": "Domestic Beer (0.5L Bottle)", "Price": "1.07\u00a0$"},
        {"City": "Asuncion", "Item": "Public Transport (One Way Ticket)", "Price": "0.49\u00a0$"},
        {"City": "Asuncion", "Item": "Public Transport (Monthly)", "Price": "21.57\u00a0$"},
        {"City": "Asuncion", "Item": "Petrol (1L)", "Price": "1.12\u00a0$"},
        {"City": "Asuncion", "Item": "Mobile Plan (10GB+ Data, Monthly)", "Price": "15.59\u00a0$"},
        {"City": "Asuncion", "Item": "Internet (60 Mbps, Unlimited Data, Monthly)", "Price": "18.57\u00a0$"},
        {"City": "Asuncion", "Item": "Gym Membership (Monthly)", "Price": "30.28\u00a0$"},
        {"City": "Asuncion", "Item": "Tennis Court Rent (1hr)", "Price": "11.12\u00a0$"},
        {"City": "Asuncion", "Item": "Cinema International Release", "Price": "6.06\u00a0$"},
        {"City": "Asuncion", "Item": "Daycare / Preschool (1 Month)", "Price": "165.08\u00a0$"},
        {"City": "Asuncion", "Item": "International Primary School (1 Year)", "Price": "3,436.45\u00a0$"},
        {"City": "Asuncion", "Item": "Pair of Jeans", "Price": "39.76\u00a0$"},
        {"City": "Asuncion", "Item": "Summer Dress Chain Store", "Price": "26.62\u00a0$"},
        {"City": "Asuncion", "Item": "Mens Leather Business Shoes", "Price": "69.63\u00a0$"},
        {"City": "Asuncion", "Item": "Rent 1 Bedroom Apartment City Centre", "Price": "362.12\u00a0$"},
        {"City": "Asuncion", "Item": "Rent 1 Bedroom Apartment Outside City Centre", "Price": "272.89\u00a0$"},
        {"City": "Asuncion", "Item": "Rent 3 Bedroom Apartment City Centre", "Price": "685.78\u00a0$"},
        {"City": "Asuncion", "Item": "Rent 3 Bedroom Apartment Outside City Centre", "Price": "610.63\u00a0$"},
        {"City": "Asuncion", "Item": "Price per Square Meter to Buy Apartment in City Centre", "Price": "1,118.53\u00a0$"},
        {"City": "Asuncion", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": "933.23\u00a0$"},
        {'City': "Asuncion", 'Item': 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)', 'Price': "9.67"}]).encode('utf-8')))}
    }