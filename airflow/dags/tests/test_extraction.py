import json
import datetime
import pytest
import requests
import requests_mock
from scripts.extraction import *
from tests.fixtures.fixtures_testing import *

def test_extract_cities(requests_mock, mock_extract_cities_html, mock_countries, mock_environment_variables, mock_boto3_s3):
    # Mock request output
    requests_mock.get('https://www.numbeo.com/cost-of-living/country_result.jsp?country=Australia', text = mock_extract_cities_html)
    
    # Expected variables generated by function
    current_date = datetime.date.today().strftime('%Y%m%d')
    expected_object_name = f'cities{current_date}'
    expected_extracted_cities_json = json.dumps([{'Australia': 'Canberra'}, {'Australia': 'Adelaide'}, {'Australia': 'Perth'}, 
    {'Australia': 'Brisbane'}, {'Australia':'Sydney'}, {'Australia':'Melbourne'}, {'Australia':'Newcastle'},
    {'Australia':'Gold Coast'}, {'Australia':'Hobart'}])
    
    # Test function
    extract_cities(mock_countries)
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = expected_object_name, Body = expected_extracted_cities_json)

def test_extract_currency_conversion_rates(requests_mock, mock_boto3_s3, mock_currency_conversion_rates_html, mock_environment_variables):
    # Mock request output
    requests_mock.get('https://www.numbeo.com/common/currency_settings.jsp', text = mock_currency_conversion_rates_html)

    # Expected variables generated by function
    current_date = datetime.date.today().strftime('%Y%m%d')
    expected_object_name = f'currency_conversion_rates{current_date}'
    expected_currency_conversion_rates_json = json.dumps([{"AED": "3.67"}, {"ALL": "99.54"}, {"AMD": "383.76"}, {"AUD": "1.55"}, {"AZN": "1.70"}, {"BAM": "1.83"}, 
    {"BGN": "1.83"}, {"BHD": "0.38"}, {"BRL": "4.86"}, {"BYN": "2.52"}, {"CAD": "1.35"}, {"CHF": "0.90"}, {"CLP": "886.62"}, {"CNY": "7.29"}, {"COP": "3,925.43"}, 
    {"CZK": "22.87"}, {"DKK": "6.98"}, {"EUR": "0.94"}, {"GBP": "0.81"}, {"GEL": "2.64"}, {"HKD": "7.82"}, {"HUF": "358.82"}, {"ILS": "3.82"}, {"ISK": "135.87"}, 
    {"JPY": "147.75"}, {"KRW": "1,323.71"}, {"MDL": "17.92"}, {"MKD": "57.58"}, {"MOP": "8.05"}, {"MXN": "17.13"}, {"MYR": "4.69"}, {"NOK": "10.82"}, {"NZD": "1.69"}, 
    {"OMR": "0.38"}, {"PLN": "4.34"}, {"PYG": "7,258.93"}, {"QAR": "3.64"}, {"RON": "4.65"}, {"RSD": "109.81"}, {"RUB": "96.59"}, {"SAR": "3.75"}, {"SEK": "11.16"}, 
    {"SGD": "1.36"}, {"THB": "35.78"}, {"TRY": "27.01"}, {"TWD": "32.03"}, {"UAH": "36.86"}, {"UYU": "38.07"}])

    # Test function
    extract_currency_conversion_rates()
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = expected_object_name, Body = expected_currency_conversion_rates_json)

def test_extract_livingcost_prices_from_city(requests_mock, mock_environment_variables, mock_boto3_s3, mock_livingcost_prices_perth_html):
    # Mock request output
    requests_mock.get('https://livingcost.org/cost/australia/perth', text = mock_livingcost_prices_perth_html)

    # Expected variables generated by function
    current_date = datetime.date.today().strftime('%Y%m%d')
    expected_object_name = f'livingcost_price_info{current_date}'
    expected_livingcost_price_info_json = json.dumps([{'City': 'Perth', 'Item': 'Lunch', 'Price': '$15.4'},
        {'City': 'Perth', 'Item': 'Coke (0.5L)', 'Price': '$2.95'},
        {'City': 'Perth', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Price': '$124' },
        {'City': 'Perth', 'Item': 'Electricity, Heating, Cooling, Water and Garbage (Family)', 'Price': '$216'},
        {'City': 'Perth', 'Item': 'Taxi (8km)', 'Price': '$17.4'},
        {'City': 'Perth', 'Item': 'Water (1L)', 'Price': '$1.43'},
        {'City': 'Perth', 'Item': 'Wine (750ml Bottle Mid Range)', 'Price': '$13.4'},
        {'City': 'Perth', 'Item': 'Brand Sneakers', 'Price': '$139'}])

    # Test function
    extract_livingcost_prices_from_city()
    mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'cities{current_date}')
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = expected_object_name, Body = expected_livingcost_price_info_json)

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
    mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'cities{current_date}')
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = expected_object_name, Body = expected_numbeo_price_info_json)