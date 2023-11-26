import requests
import json
import os
import boto3
import datetime
import re
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from utils.aws_utils import *

# Load S3 environment variables
load_dotenv()

# Extract relevant currencies with conversion rates
def extract_currency_conversion_rates() -> None:
    # Scraped conversion rates USD -> local
    currency_conversion_rates = []

    # Abbreviations to extract
    abbreviations = ['AED', 'AUD', 'BAM', 'BGN', 'BHD', 'BRL', 'CAD',
    'CHF', 'CLP', 'CNY', 'COP', 'CRC', 'CZK', 'DKK', 'EUR', 'GEL', 'HKD', 'HUF', 'ISK', 'ILS', 'JPY',
    'KRW', 'KWD', 'MOP', 'MYR', 'MXN', 'NOK', 'NZD', 'OMR', 'PLN', 'QAR', 'RON', 'RUB',
    'SAR', 'RSD', 'SGD', 'SEK', 'THB', 'TRY', 'TWD', 'UAH', 'GBP', 'UYU', 'PYG']
    
    # Request
    response = requests.get('https://www.numbeo.com/common/currency_settings.jsp')
    
    # Parse html
    currency_conversion_rates_html = BeautifulSoup(response.text, 'html.parser')
    rows = currency_conversion_rates_html.find('tbody').find_all('tr')
    for row in rows:
        abbreviation = row.find('td').text
        if abbreviation in abbreviations:
            conversion_rate = row.find_all('td', {'style': 'text-align: right'})[1].text
            currency_conversion_rates.append({'Abbreviation': abbreviation , 'USD_to_local': conversion_rate})

    # Load data to S3 raw bucket
    put_data(file_prefix='currency_conversion_rates', data=currency_conversion_rates, bucket_type='raw')

# Extract livingcost prices from city
def extract_livingcost_prices_from_city() -> None:

    # Retrieve latest cities file
    locations = get_data(file_prefix='locations.json')

    # Store livingcost price info for each city
    livingcost_price_info = []

    for location in locations:
        # Format country and city for request
        country_name = location['Country'].split()
        city_name = location['City'].split()
        capitalised_country_name = [word.capitalize() for word in country_name]
        capitalised_city_name = [word.capitalize() for word in city_name]
        formatted_country_name = '-'.join(capitalised_country_name)
        formatted_city_name = '-'.join(capitalised_city_name)

        # Request Country Page based on formatted_country_name
        if not (formatted_country_name == 'Hong-Kong' or formatted_country_name == 'Macau'):
            response = requests.get(f'https://livingcost.org/cost/{formatted_country_name}')
            livingcost_country_page_html = BeautifulSoup(response.text, 'html.parser')
            city_urls = []
            ol_elements = livingcost_country_page_html.find_all('ol', {'class': 'row geo-gutters mb-4 list-unstyled'})
            for ol in ol_elements:
                li_elements = ol.find_all('li')

                for li in li_elements:
                    div_element = li.find_all('div')[0]
                    a_element = div_element.find('a', href = True)
                    city_urls.append(a_element['href'])

            pattern = f'.*{formatted_city_name}.*'
            for url in city_urls:
                if re.search(pattern, url, re.IGNORECASE):
                    url_to_extract = url
                    break
        # Special case for Hong Kong and Macau
        else:
            if formatted_city_name == 'Hong-Kong':
                url_to_extract = f'https://livingcost.org/cost/china/hong-kong'
            else:
                url_to_extract = f'https://livingcost.org/cost/china/macau'
        
        # Request city prices page
        response = requests.get(url_to_extract)
        livingcost_city_page_html = BeautifulSoup(response.text, 'html.parser')
        
        # Prices from Eating Out
        eating_out_table = livingcost_city_page_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[0].find('tbody').find_all('tr')
        lunch = eating_out_table[0].find('div', {'class': 'bar-table text-center'}).find('span').text
        coke = eating_out_table[5].find('div', {'class': 'bar-table text-center'}).find('span').text

        # Prices from Utilities
        utilities_table = livingcost_city_page_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[1].find('tbody').find_all('tr')
        utilities_one_person = utilities_table[4].find('div', {'class': 'bar-table text-center'}).find('span').text
        utilities_family = utilities_table[5].find('div', {'class': 'bar-table text-center'}).find('span').text

        # Prices from Transportation
        transportation_table = livingcost_city_page_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[2].find('tbody').find_all('tr')
        taxi = transportation_table[2].find('div', {'class': 'bar-table text-center'}).find('span').text

        # Prices from Groceries
        groceries_table = livingcost_city_page_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[3].find('tbody').find_all('tr')
        water = groceries_table[13].find('div', {'class': 'bar-table text-center'}).find('span').text
        wine = groceries_table[15].find('div', {'class': 'bar-table text-center'}).find('span').text

        # Prices from other
        other_table = livingcost_city_page_html.find_all('table', {'class': 'table table-sm table-striped table-hover'})[4].find('tbody').find_all('tr')
        brand_sneakers = other_table[5].find('div', {'class': 'bar-table text-center'}).find('span').text
        
        # Add scraped data to list
        livingcost_price_info.extend([{'City': location['City'], 'Item': 'Lunch', 'Price': lunch},
        {'City': location['City'], 'Item': 'Coke (0.5L)', 'Price': coke},
        {'City': location['City'], 'Item': 'Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Price': utilities_one_person},
        {'City': location['City'], 'Item': 'Electricity, Heating, Cooling, Water and Garbage (Family)', 'Price': utilities_family},
        {'City': location['City'], 'Item': 'Taxi (8km)', 'Price': taxi},
        {'City': location['City'], 'Item': 'Water (1L)', 'Price': water},
        {'City': location['City'], 'Item': 'Wine (750ml Bottle Mid Range)', 'Price': wine},
        {'City': location['City'], 'Item': 'Brand Sneakers', 'Price': brand_sneakers}])

    # Load data to S3 raw bucket
    put_data(file_prefix='livingcost_price_info', data = livingcost_price_info, bucket_type='raw')

# Extract numbeo prices
def extract_numbeo_prices_from_city() -> None:

    # Retrieve latest cities file
    locations = get_data(file_prefix='locations.json')

    # Store numbeo price info for each city
    numbeo_price_info = []

    for location in locations:
        # Format city for request
        city_name = location['City'].split()
        capitalised_city_name = [word.capitalize() for word in city_name]
        formatted_city_name = '-'.join(capitalised_city_name)
        country_name = location['Country'].split()
        capitalised_country_name = [word.capitalize() for word in country_name]
        formatted_country_name = '-'.join(capitalised_country_name)

        # Request + special cases to deal with when scraping
        if formatted_city_name in ['Vaduz', 'Aarhus', 'Crete', 'San-Marino', 'Kawasaki', 'Malacca', 'Sochi', 'Donetsk', 'Mar-Del-Plata']:
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/{formatted_city_name}-{formatted_country_name}?displayCurrency=USD')
        elif formatted_city_name == 'Seville':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Sevilla?displayCurrency=USD')
        elif formatted_city_name == 'Zaragoza':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Zaragoza-Saragossa?displayCurrency=USD')
        elif formatted_city_name == 'Macau':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Macao?displayCurrency=USD')
        elif formatted_city_name == 'Jeddah':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Jeddah-Jiddah?displayCurrency=USD')
        elif formatted_city_name == 'Kyiv':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Kiev?displayCurrency=USD')
        elif formatted_city_name == 'Tel-Aviv':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Tel-Aviv-Yafo?displayCurrency=USD')
        elif formatted_city_name == 'Playa-Del-Carmen':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Playa-del-Carmen?displayCurrency=USD')
        elif formatted_city_name == 'Krakow':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Krakow-Cracow?displayCurrency=USD')
        elif formatted_city_name == 'New-York-City':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/New-York?displayCurrency=USD')
        elif formatted_city_name == 'Kansas':
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/Kansas-City?displayCurrency=USD')
        else:
            response = requests.get(f'https://www.numbeo.com/cost-of-living/in/{formatted_city_name}?displayCurrency=USD')
        
        # Extract price information from relevant items
        numbeo_prices_city_html = BeautifulSoup(response.text, 'html.parser')
        prices_table = numbeo_prices_city_html.find('table', {'class': 'data_wide_table new_bar_table'}).find_all('tr')

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

        # Prices from buy apartment price
        price_per_sqm_apartment_city_centre = prices_table[60].find('td', {'style': 'text-align: right'}).find('span').text
        price_per_sqm_apartment_outside_city_centre = prices_table[61].find('td', {'style': 'text-align: right'}).find('span').text

        # Mortgage interest rate
        mortgage_interest_rate = prices_table[64].find('td', {'style': 'text-align: right'}).find('span').text

        # Add scraped data to list
        numbeo_price_info.extend([{'City': location['City'], 'Item': 'Dinner (2 People Mid Range Restaurant)', 'Price': meal_two_people_mid_range},
        {'City': location['City'], 'Item': 'Domestic Draught (0.5L)', 'Price': domestic_draught},
        {'City': location['City'], 'Item': 'Cappuccino (Regular)', 'Price': cappuccino},
        {'City': location['City'], 'Item': 'Milk (1L)', 'Price': milk},
        {'City': location['City'], 'Item': 'Bread (500g)', 'Price': bread},
        {'City': location['City'], 'Item': 'Rice (1kg)', 'Price': rice},
        {'City': location['City'], 'Item': 'Eggs (x12)', 'Price': eggs},
        {'City': location['City'], 'Item': 'Cheese (1kg)', 'Price': cheese},
        {'City': location['City'], 'Item': 'Chicken Fillets (1kg)', 'Price': chicken},
        {'City': location['City'], 'Item': 'Beef Round (1kg)', 'Price': beef},
        {'City': location['City'], 'Item': 'Apples (1kg)', 'Price': apples},
        {'City': location['City'], 'Item': 'Banana (1kg)', 'Price': banana},
        {'City': location['City'], 'Item': 'Oranges (1kg)', 'Price': oranges},
        {'City': location['City'], 'Item': 'Tomato (1kg)', 'Price': tomato},
        {'City': location['City'], 'Item': 'Potato (1kg)', 'Price': potato},
        {'City': location['City'], 'Item': 'Onion (1kg)', 'Price': onion},
        {'City': location['City'], 'Item': 'Lettuce (1 Head)', 'Price': lettuce},
        {'City': location['City'], 'Item': 'Domestic Beer (0.5L Bottle)', 'Price': domestic_beer},
        {'City': location['City'], 'Item': 'Public Transport (One Way Ticket)', 'Price': one_way_ticket},
        {'City': location['City'], 'Item': 'Public Transport (Monthly)', 'Price': monthly_pass},
        {'City': location['City'], 'Item': 'Petrol (1L)', 'Price': petrol},
        {'City': location['City'], 'Item': 'Mobile Plan (10GB+ Data, Monthly)', 'Price': mobile_plan_monthly},
        {'City': location['City'], 'Item': 'Internet (60 Mbps, Unlimited Data, Monthly)', 'Price': internet},
        {'City': location['City'], 'Item': 'Gym Membership (Monthly)', 'Price': gym_membership_monthly},
        {'City': location['City'], 'Item': 'Tennis Court Rent (1hr)', 'Price': tennis_court_one_hour},
        {'City': location['City'], 'Item': 'Cinema International Release', 'Price': cinema},
        {'City': location['City'], 'Item': 'Daycare / Preschool (1 Month)', 'Price': preschool},
        {'City': location['City'], 'Item': 'International Primary School (1 Year)', 'Price': international_primary_school},
        {'City': location['City'], 'Item': 'Pair of Jeans', 'Price': jeans},
        {'City': location['City'], 'Item': 'Summer Dress Chain Store', 'Price': summer_dress},
        {'City': location['City'], 'Item': 'Mens Leather Business Shoes', 'Price': mens_leather_business_shoes},
        {'City': location['City'], 'Item': 'Rent 1 Bedroom Apartment City Centre', 'Price': apartment_one_bedroom_city},
        {'City': location['City'], 'Item': 'Rent 1 Bedroom Apartment Outside City Centre', 'Price': apartment_one_bedroom_outside_city},
        {'City': location['City'], 'Item': 'Rent 3 Bedroom Apartment City Centre', 'Price': apartment_three_bedroom_city},
        {'City': location['City'], 'Item': 'Rent 3 Bedroom Apartment Outside City Centre', 'Price': apartment_three_bedroom_outside_city},
        {'City': location['City'], 'Item': 'Price per Square Meter to Buy Apartment in City Centre', 'Price': price_per_sqm_apartment_city_centre},
        {'City': location['City'], 'Item': 'Price per Square Meter to Buy Apartment Outside of Centre', 'Price': price_per_sqm_apartment_outside_city_centre},
        {'City': location['City'], 'Item': 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)', 'Price': mortgage_interest_rate}])
    
    # Load data to S3 raw bucket
    put_data(file_prefix='numbeo_price_info', data=numbeo_price_info, bucket_type='raw')
