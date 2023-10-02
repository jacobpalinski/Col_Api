import requests
import json
import os
import boto3
import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

def extract_livingcost_prices_from_city():
     # Load S3 environment variables
    load_dotenv()
    
    # Connect to S3 bucket
    boto3_s3 = boto3.client('s3', aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY'))

    # Retrieve latest cities file
    current_date = datetime.date.today().strftime('%Y%m%d')
    file = boto3_s3.get_object(Bucket = os.environ.get('S3_BUCKET_RAW'), Key = f'cities{current_date}')
    contents = file['Body'].read().decode('utf-8')
    cities = json.loads(contents)

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
    livingcost_price_info_json = json.dumps(livingcost_price_info)
    current_date = datetime.date.today().strftime('%Y%m%d')
    object_name = f'livingcost_price_info{current_date}'
    boto3_s3.put_object(Bucket = os.environ.get('S3_BUCKET_RAW'), Key = object_name, Body = livingcost_price_info_json)
        
    
