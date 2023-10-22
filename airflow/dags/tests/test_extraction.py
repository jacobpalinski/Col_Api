import json
import datetime
import pytest
import requests
import requests_mock
from scripts.extraction import *
from tests.fixtures.fixtures_testing import *

def test_extract_currency_conversion_rates(requests_mock, mock_boto3_s3, mock_currency_conversion_rates_html, mock_environment_variables, current_date):
    # Mock request output
    requests_mock.get('https://www.numbeo.com/common/currency_settings.jsp', text = mock_currency_conversion_rates_html)

    # Expected variables generated by function
    expected_object_name = f'currency_conversion_rates{current_date}'
    expected_currency_conversion_rates_json = json.dumps([{"Abbreviation": "AED", "USD_to_local": "3.67"}, {"Abbreviation": "AUD", "USD_to_local": "1.55"}, 
    {"Abbreviation": "BAM", "USD_to_local": "1.83"}, {"Abbreviation": "BGN", "USD_to_local": "1.83"}, {"Abbreviation": "BHD", "USD_to_local": "0.38"},
    {"Abbreviation": "BRL", "USD_to_local": "4.86"}, {"Abbreviation": "CAD", "USD_to_local": "1.35"}, {"Abbreviation": "CHF", "USD_to_local": "0.90"}, 
    {"Abbreviation": "CLP", "USD_to_local": "886.62"}, {"Abbreviation": "CNY", "USD_to_local": "7.29"}, {"Abbreviation": "COP", "USD_to_local": "3,925.43"}, 
    {"Abbreviation": "CRC", "USD_to_local": "529.05"}, {"Abbreviation": "CZK", "USD_to_local": "22.87"}, {"Abbreviation": "DKK", "USD_to_local": "6.98"}, 
    {"Abbreviation": "EUR", "USD_to_local": "0.94"}, {"Abbreviation": "GBP", "USD_to_local": "0.81"}, {"Abbreviation": "GEL", "USD_to_local": "2.64"}, 
    {"Abbreviation": "HKD", "USD_to_local": "7.82"}, {"Abbreviation": "HUF", "USD_to_local": "358.82"}, {"Abbreviation": "ILS", "USD_to_local": "3.82"}, 
    {"Abbreviation": "ISK", "USD_to_local": "135.87"}, {"Abbreviation": "JPY", "USD_to_local": "147.75"}, {"Abbreviation": "KRW", "USD_to_local": "1,323.71"}, 
    {"Abbreviation": "KWD", "USD_to_local": "0.31"}, {"Abbreviation": "MOP", "USD_to_local": "8.05"}, {"Abbreviation": "MXN", "USD_to_local": "17.13"}, 
    {"Abbreviation": "MYR", "USD_to_local": "4.69"}, {"Abbreviation": "NOK", "USD_to_local": "10.82"}, {"Abbreviation": "NZD", "USD_to_local": "1.69"}, 
    {"Abbreviation": "OMR", "USD_to_local": "0.38"}, {"Abbreviation": "PLN", "USD_to_local": "4.34"}, {"Abbreviation": "PYG", "USD_to_local": "7,258.93"}, 
    {"Abbreviation": "QAR", "USD_to_local": "3.64"}, {"Abbreviation": "RON", "USD_to_local": "4.65"}, {"Abbreviation": "RSD", "USD_to_local": "109.81"}, 
    {"Abbreviation": "RUB", "USD_to_local": "96.59"}, {"Abbreviation": "SAR", "USD_to_local": "3.75"}, {"Abbreviation": "SEK", "USD_to_local": "11.16"}, 
    {"Abbreviation": "SGD", "USD_to_local": "1.36"}, {"Abbreviation": "THB", "USD_to_local": "35.78"}, {"Abbreviation": "TRY", "USD_to_local": "27.01"}, 
    {"Abbreviation": "TWD", "USD_to_local": "32.03"}, {"Abbreviation": "UAH", "USD_to_local": "36.86"}, {"Abbreviation": "UYU", "USD_to_local": "38.07"}])

    # Test function
    extract_currency_conversion_rates()
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = expected_object_name, Body = expected_currency_conversion_rates_json)

def test_extract_livingcost_prices_from_city(requests_mock, mock_environment_variables, mock_boto3_s3, mock_livingcost_australia_html, mock_livingcost_new_zealand_html,
mock_livingcost_china_html, mock_livingcost_paraguay_html, mock_livingcost_prices_perth_html, mock_livingcost_prices_auckland_html, mock_livingcost_prices_hong_kong_html,
mock_livingcost_prices_asuncion_html, current_date):
    
    # Mock request output
    requests_mock.get('https://livingcost.org/cost/Australia', text = mock_livingcost_australia_html)
    requests_mock.get('https://livingcost.org/cost/New-Zealand', text = mock_livingcost_new_zealand_html)
    requests_mock.get('https://livingcost.org/cost/China', text = mock_livingcost_china_html)
    requests_mock.get('https://livingcost.org/cost/Paraguay', text = mock_livingcost_paraguay_html)
    requests_mock.get('https://livingcost.org/cost/australia/perth', text = mock_livingcost_prices_perth_html)
    requests_mock.get('https://livingcost.org/cost/new-zealand/auckland', text = mock_livingcost_prices_auckland_html)
    requests_mock.get('https://livingcost.org/cost/china/hong-kong', text = mock_livingcost_prices_hong_kong_html)
    requests_mock.get('https://livingcost.org/cost/paraguay/asuncion', text = mock_livingcost_prices_asuncion_html)

    # Expected variables generated by function
    expected_object_name = f'livingcost_price_info{current_date}'
    expected_livingcost_price_info_json = json.dumps([{'City': 'Perth', 'Item': 'Lunch', 'Price': '$15.4'},
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
    {'City': 'Asuncion', 'Item': 'Brand Sneakers', 'Price': '$85.6'}])

    # Test function
    extract_livingcost_prices_from_city()
    mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'locations.json')
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = expected_object_name, Body = expected_livingcost_price_info_json)

def test_extract_numbeo_prices_from_city(requests_mock, mock_environment_variables, mock_boto3_s3, mock_numbeo_prices_perth_html, 
mock_numbeo_prices_auckland_html, mock_numbeo_prices_hong_kong_html, mock_numbeo_prices_asuncion_html, current_date):
    # Mock request output
    requests_mock.get('https://www.numbeo.com/cost-of-living/in/Perth?displayCurrency=USD', text = mock_numbeo_prices_perth_html)
    requests_mock.get('https://www.numbeo.com/cost-of-living/in/Auckland?displayCurrency=USD', text = mock_numbeo_prices_auckland_html)
    requests_mock.get('https://www.numbeo.com/cost-of-living/in/Hong-Kong?displayCurrency=USD', text = mock_numbeo_prices_hong_kong_html)
    requests_mock.get('https://www.numbeo.com/cost-of-living/in/Asuncion?displayCurrency=USD', text = mock_numbeo_prices_asuncion_html)

    # Expected variables generated by function
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
    {"City": "Perth", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": "5,395.77\u00a0$"},
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
    {"City": "Auckland", "Item": "Cigarettes (20 Pack Malboro)", "Price": "23.34\u00a0$"},
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
    {"City": "Hong Kong", "Item": "Cigarettes (20 Pack Malboro)", "Price": "9.97\u00a0$"},
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
    {"City": "Asuncion", "Item": "Cigarettes (20 Pack Malboro)", "Price": "1.50\u00a0$"},
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
    {"City": "Asuncion", "Item": "Price per Square Meter to Buy Apartment Outside of Centre", "Price": "933.23\u00a0$"}])
    
    # Test function
    extract_numbeo_prices_from_city()
    mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'locations.json')
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = expected_object_name, Body = expected_numbeo_price_info_json)