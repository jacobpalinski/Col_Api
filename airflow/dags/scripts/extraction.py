import requests
import json
import os
import boto3
import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from utils.aws_utils import *

# Load S3 environment variables
load_dotenv()

# Countries to extract cities from
countries = ['United Arab Emirates', 'Albania', 'Armenia', 'Australia', 'Azerbaijan', 'Bosnia and Herzegovina', 'Bahrain', 'Bulgaria',
    'Belarus', 'Brazil', 'Canada', 'Switzerland', 'Liechtenstein', 'Chile', 'China', 'Colombia', 'Czech Republic', 'Denmark', 'Faroe Islands', 'Andorra',
    'Austria', 'Belgium', 'Croatia', 'Cyprus', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Ireland', 'Italy', 'Kosovo', 'Latvia',
    'Lithuania', 'Luxembourg', 'Malta', 'Montenegro', 'Monaco', 'Netherlands', 'Portugal', 'San Marino', 'Slovakia', 'Slovenia', 'Spain',
    'Georgia', 'Hong Kong (China)', 'Hungary', 'Israel', 'Japan', 'South Korea', 'Macau', 'Malaysia', 'Mexico', 'Moldova', 'New Zealand',
    'North Macedonia' 'Norway', 'Oman', 'Poland', 'Qatar', 'Romania', 'Russia', 'Saudi Arabia', 'Serbia', 'Singapore', 'Sweden', 'Taiwan',
    'Thailand', 'Turkey', 'Ukraine', 'United Kingdom', 'Gibraltar', 'Isle of Man', 'Jersey', 'Uruguay', 'United States', 'Ecuador', 'Paraguay', 'Argentina']

def extract_cities(countries: list):
    # Cities
    cities = []

    for country in countries:
        # Request
        response = requests.get(f'https://www.numbeo.com/cost-of-living/country_result.jsp?country={country}')
        
        # Parse Html
        numbeo_country_html = BeautifulSoup(response.text, 'html.parser')
        rows = numbeo_country_html.find('table', {'id': 't2'}).find('tbody').find_all('tr')
        for row in rows:
            city = row.find('a').text
            cities.append({country: city})

    # Load data to S3 raw bucket
    put_data(file_prefix = 'cities', data = cities)

def extract_currency_conversion_rates():
    # Scraped conversion rates USD -> local
    currency_conversion_rates = []

    # Abbreviations to extract
    abbreviations = ['AED','ALL','AMD', 'AUD', 'AZN', 'BAM', 'BGN', 'BHD', 'BRL', 'BYN', 'CAD',
    'CHF', 'CLP', 'CNY', 'COP', 'CZK', 'DKK', 'EUR', 'GEL', 'HKD', 'HUF', 'ISK', 'ILS', 'JPY',
    'KRW', 'MOP', 'MYR', 'MXN', 'MDL', 'NZD', 'MKD', 'NOK', 'OMR', 'PLN', 'QAR', 'RON', 'RUB',
    'SAR', 'RSD', 'SGD', 'SEK', 'CHF', 'TWD', 'THB', 'TRY', 'UAH', 'GBP', 'UYU', 'PYG']
    
    # Request
    response = requests.get('https://www.numbeo.com/common/currency_settings.jsp')
    
    # Parse html
    currency_conversion_rates_html = BeautifulSoup(response.text, 'html.parser')
    rows = currency_conversion_rates_html.find('tbody').find_all('tr')
    for row in rows:
        abbreviation = row.find('td').text
        if abbreviation in abbreviations:
            conversion_rate = row.find_all('td', {'style': 'text-align: right'})[1].text
            currency_conversion_rates.append({abbreviation : conversion_rate})

    # Load data to S3 raw bucket
    put_data(file_prefix = 'currency_conversion_rates', data = currency_conversion_rates)

def extract_livingcost_prices_from_city():

    # Retrieve latest cities file
    cities = get_data(file_prefix = 'cities')

    livingcost_price_info = []

    for city in cities:
        # Request
        response = requests.get(f'https://livingcost.org/cost/australia/{city}')
        
        # Extract price information from relevant items
        livingcost_prices_city_html = BeautifulSoup(response.text, 'html.parser')
        
        # Prices from Eating Out
        eating_out_table = livingcost_prices_city_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[0].find('tbody').find_all('tr')
        lunch = eating_out_table[0].find('div', {'class': 'bar-table text-center'}).find('span').text
        coke = eating_out_table[5].find('div', {'class': 'bar-table text-center'}).find('span').text

        # Prices from Utilities
        utilities_table = livingcost_prices_city_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[1].find('tbody').find_all('tr')
        utilities_one_person = utilities_table[4].find('div', {'class': 'bar-table text-center'}).find('span').text
        utilities_family = utilities_table[5].find('div', {'class': 'bar-table text-center'}).find('span').text

        # Prices from Transportation
        transportation_table = livingcost_prices_city_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[2].find('tbody').find_all('tr')
        taxi = transportation_table[2].find('div', {'class': 'bar-table text-center'}).find('span').text

        # Prices from Groceries
        groceries_table = livingcost_prices_city_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[3].find('tbody').find_all('tr')
        water = groceries_table[13].find('div', {'class': 'bar-table text-center'}).find('span').text
        wine = groceries_table[15].find('div', {'class': 'bar-table text-center'}).find('span').text

        # Prices from other
        other_table = livingcost_prices_city_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[4].find('tbody').find_all('tr')
        brand_sneakers = other_table[5].find('div', {'class': 'bar-table text-center'}).find('span').text
        
        livingcost_price_info.extend([{'City': city, 'Item': 'Lunch', 'Price': lunch},
        {'City': city, 'Item': 'Coke (0.5L)', 'Price': coke},
        {'City': city, 'Item': 'Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Price': utilities_one_person },
        {'City': city, 'Item': 'Electricity, Heating, Cooling, Water and Garbage (Family)', 'Price': utilities_family},
        {'City': city, 'Item': 'Taxi (8km)', 'Price': taxi},
        {'City': city, 'Item': 'Water (1L)', 'Price': water},
        {'City': city, 'Item': 'Wine (750ml Bottle Mid Range)', 'Price': wine},
        {'City': city, 'Item': 'Brand Sneakers', 'Price': brand_sneakers}])

    # Load data to S3 raw bucket
    put_data(file_prefix = 'livingcost_price_info', data = livingcost_price_info)

def extract_numbeo_prices_from_city():

    # Retrieve latest cities file
    cities = get_data(file_prefix = 'cities')

    numbeo_price_info = []

    for city in cities:
        # Request
        response = requests.get(f'https://www.numbeo.com/cost-of-living/in/{city}?displayCurrency=USD')
        
        # Extract price information from relevant items
        numbeo_prices_city_html = BeautifulSoup(response.text, 'html.parser')
        prices_table = numbeo_prices_city_html.find('table', {'class': 'data_wide_table new_bar_table'}).find('tbody').find_all('tr')

        # Prices from restaurants
        meal_two_people_mid_range = prices_table[2].find('td', {'style': 'text-align: right'}).find('span').text
        domestic_draught = prices_table[4].find('td', {'style': 'text-align: right'}).find('span').text
        cappuccino = prices_table[6].find('td', {'style': 'text-align: right'}).find('span').text
        
        # Prices from markets
        milk = prices_table[10].find('td', {'style': 'text-align: right'}).find('span').text
        bread = prices_table[11].find('td', {'style': 'text-align: right'}).find('span').text
        rice = prices_table[12].find('td', {'style': 'text-align: right'}).find('span').text
        eggs = prices_table[13].find('td', {'style': 'text-align: right'}).find('span').text
        cheese = prices_table[14].find('td', {'style': 'text-align: right'}).find('span').text
        chicken = prices_table[15].find('td', {'style': 'text-align: right'}).find('span').text
        beef = prices_table[16].find('td', {'style': 'text-align: right'}).find('span').text
        apples = prices_table[17].find('td', {'style': 'text-align: right'}).find('span').text
        banana = prices_table[18].find('td', {'style': 'text-align: right'}).find('span').text
        oranges = prices_table[19].find('td', {'style': 'text-align: right'}).find('span').text
        tomato = prices_table[20].find('td', {'style': 'text-align: right'}).find('span').text
        potato = prices_table[21].find('td', {'style': 'text-align: right'}).find('span').text
        onion = prices_table[22].find('td', {'style': 'text-align: right'}).find('span').text
        lettuce = prices_table[23].find('td', {'style': 'text-align: right'}).find('span').text
        domestic_beer = prices_table[26].find('td', {'style': 'text-align: right'}).find('span').text
        cigarettes = prices_table[28].find('td', {'style': 'text-align: right'}).find('span').text
        
        # Prices from transportation
        one_way_ticket = prices_table[30].find('td', {'style': 'text-align: right'}).find('span').text
        monthly_pass = prices_table[31].find('td', {'style': 'text-align: right'}).find('span').text
        petrol = prices_table[35].find('td', {'style': 'text-align: right'}).find('span').text
        
        # Prices from utilities
        mobile_plan_monthly = prices_table[40].find('td', {'style': 'text-align: right'}).find('span').text
        internet = prices_table[41].find('td', {'style': 'text-align: right'}).find('span').text
        
        # Prices from leisure
        gym_membership_monthly = prices_table[43].find('td', {'style': 'text-align: right'}).find('span').text
        tennis_court_one_hour = prices_table[44].find('td', {'style': 'text-align: right'}).find('span').text
        cinema = prices_table[45].find('td', {'style': 'text-align: right'}).find('span').text
        
        # Prices from childcare
        preschool = prices_table[47].find('td', {'style': 'text-align: right'}).find('span').text
        international_primary_school = prices_table[48].find('td', {'style': 'text-align: right'}).find('span').text
        
        # Prices from clothing
        jeans = prices_table[50].find('td', {'style': 'text-align: right'}).find('span').text
        summer_dress = prices_table[51].find('td', {'style': 'text-align: right'}).find('span').text
        mens_leather_business_shoes = prices_table[53].find('td', {'style': 'text-align: right'}).find('span').text
        
        # Prices from rent per month
        apartment_one_bedroom_city = prices_table[55].find('td', {'style': 'text-align: right'}).find('span').text
        apartment_one_bedroom_outside_city = prices_table[56].find('td', {'style': 'text-align: right'}).find('span').text
        apartment_three_bedroom_city = prices_table[57].find('td', {'style': 'text-align: right'}).find('span').text
        apartment_three_bedroom_outside_city = prices_table[58].find('td', {'style': 'text-align: right'}).find('span').text
        price_per_sqm_apartment_city_centre = prices_table[60].find('td', {'style': 'text-align: right'}).find('span').text
        price_per_sqm_apartment_outside_city_centre = prices_table[61].find('td', {'style': 'text-align: right'}).find('span').text

        numbeo_price_info.extend([{'City': city, 'Item': 'Dinner (2 People Mid Range Restaurant)', 'Price': meal_two_people_mid_range},
        {'City': city, 'Item': 'Domestic Draught (0.5L)', 'Price': domestic_draught},
        {'City': city, 'Item': 'Cappuccino (Regular)', 'Price': cappuccino},
        {'City': city, 'Item': 'Milk (1L)', 'Price': milk},
        {'City': city, 'Item': 'Bread (500g)', 'Price': bread},
        {'City': city, 'Item': 'Rice (1kg)', 'Price': rice},
        {'City': city, 'Item': 'Eggs (x12)', 'Price': eggs},
        {'City': city, 'Item': 'Cheese (1kg)', 'Price': cheese},
        {'City': city, 'Item': 'Chicken Fillets (1kg)', 'Price': chicken},
        {'City': city, 'Item': 'Beef Round (1kg)', 'Price': beef},
        {'City': city, 'Item': 'Apples (1kg)', 'Price': apples},
        {'City': city, 'Item': 'Banana (1kg)', 'Price': banana},
        {'City': city, 'Item': 'Oranges (1kg)', 'Price': oranges},
        {'City': city, 'Item': 'Tomato (1kg)', 'Price': tomato},
        {'City': city, 'Item': 'Potato (1kg)', 'Price': potato},
        {'City': city, 'Item': 'Onion (1kg)', 'Price': onion},
        {'City': city, 'Item': 'Lettuce (1 Head)', 'Price': lettuce},
        {'City': city, 'Item': 'Domestic Beer (0.5L Bottle)', 'Price': domestic_beer},
        {'City': city, 'Item': 'Cigarettes (20 Pack Malboro)', 'Price': cigarettes},
        {'City': city, 'Item': 'Public Transport (One Way Ticket)', 'Price': one_way_ticket},
        {'City': city, 'Item': 'Public Transport (Monthly)', 'Price': monthly_pass},
        {'City': city, 'Item': 'Petrol (1L)', 'Price': petrol},
        {'City': city, 'Item': 'Mobile Plan (10GB+ Data, Monthly)', 'Price': mobile_plan_monthly},
        {'City': city, 'Item': 'Internet (60 Mbps, Unlimited Data, Monthly)', 'Price': internet},
        {'City': city, 'Item': 'Gym Membership (Monthly)', 'Price': gym_membership_monthly},
        {'City': city, 'Item': 'Tennis Court Rent (1hr)', 'Price': tennis_court_one_hour},
        {'City': city, 'Item': 'Cinema International Release', 'Price': cinema},
        {'City': city, 'Item': 'Daycare / Preschool (1 Month)', 'Price': preschool},
        {'City': city, 'Item': 'International Primary School (1 Year)', 'Price': international_primary_school},
        {'City': city, 'Item': 'Pair of Jeans', 'Price': jeans},
        {'City': city, 'Item': 'Summer Dress Chain Store', 'Price': summer_dress},
        {'City': city, 'Item': 'Mens Leather Business Shoes', 'Price': mens_leather_business_shoes},
        {'City': city, 'Item': 'Rent 1 Bedroom Apartment City Centre', 'Price': apartment_one_bedroom_city},
        {'City': city, 'Item': 'Rent 1 Bedroom Apartment Outside City Centre', 'Price': apartment_one_bedroom_outside_city},
        {'City': city, 'Item': 'Rent 3 Bedroom Apartment City Centre', 'Price': apartment_three_bedroom_city},
        {'City': city, 'Item': 'Rent 3 Bedroom Apartment Outside City Centre', 'Price': apartment_three_bedroom_outside_city},
        {'City': city, 'Item': 'Price per Square Meter to Buy Apartment in City Centre', 'Price': price_per_sqm_apartment_city_centre},
        {'City': city, 'Item': 'Price per Square Meter to Buy Apartment Outside of Centre', 'Price': price_per_sqm_apartment_outside_city_centre}])

    # Load data to S3 raw bucket
    put_data(file_prefix = 'numbeo_price_info', data = numbeo_price_info)