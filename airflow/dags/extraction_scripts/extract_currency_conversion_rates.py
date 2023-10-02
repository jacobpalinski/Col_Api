import requests
import json
import os
import boto3
import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

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
    
    # Load S3 environment variables
    load_dotenv()

    # Load data to S3 raw bucket
    boto3_s3 = boto3.client('s3', aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY'))
    currency_conversion_rates_json = json.dumps(currency_conversion_rates)
    current_date = datetime.date.today().strftime('%Y%m%d')
    object_name = f'currency_conversion_rates{current_date}'
    boto3_s3.put_object(Bucket = os.environ.get('S3_BUCKET_RAW'), Key = object_name, Body = currency_conversion_rates_json)
        

