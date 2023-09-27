import datetime
import json
import os
import requests_mock
from tests.fixtures.fixtures_testing import mock_environment_variables, mock_boto3_s3, mock_numbeo_prices_perth_html
from scripts.extract_numbeo_prices import extract_numbeo_prices_from_city

def test_extract_numbeo_prices_from_city(requests_mock, mock_environment_variables, mock_boto3_s3, mock_numbeo_prices_perth_html):
    # Mock request output
    requests_mock.get('https://www.numbeo.com/cost-of-living/in/Perth?displayCurrency=USD', text = mock_numbeo_prices_perth_html)

    # Expected variables generated by function
    current_date = datetime.date.today().strftime('%Y%m%d')
    expected_object_name = f'numbeo_price_info{current_date}'
    expected_numbeo_price_info_json = json.dumps([{"City": "Perth", "Item": "Dinner (2 People Mid Range Restaurant)", "Price": "96.31\u00a0$"},
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
    {"City": "Perth", "Item": "Cigarettes (20 Pack Malboro)", "Price": "26.41\u00a0$"},
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
    {"City": "Perth", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": "5,395.77\u00a0$"}])

    # Test function
    extract_numbeo_prices_from_city()
    mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'bucket', Key = f'cities{current_date}')
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'bucket', Key = expected_object_name, Body = expected_numbeo_price_info_json)