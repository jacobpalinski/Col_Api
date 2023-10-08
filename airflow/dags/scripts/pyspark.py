import boto3
from utils.spark_utils import create_spark_session
from utils.aws_utils import *

country_abbreviation_combinations = {'United Arab Emirates': 'AED', 'Albania': 'ALL', 'Armenia': 'AMD', 'Australia': 'AUD', 'Azerbaijan': 'AZN', 
'Bosnia and Herzegovina': 'BAM', 'Bahrain': 'BHD', 'Bulgaria': 'BGN', 'Belarus': 'BRL', 'Brazil': 'BYN', 'Canada': 'CAD', 'Switzerland': 'CHF',
'Liechtenstein': 'CHF', 'Chile': 'CLP', 'China': 'CNY', 'Colombia': 'COP', 'Czech Republic': 'CZK', 'Denmark': 'DKK', 'Faroe Islands': 'DKK',
'Andorra': 'EUR', 'Austria': 'EUR', 'Belgium': 'EUR', 'Croatia': 'EUR', 'Cyprus': 'EUR', 'Estonia': 'EUR', 'Finland': 'EUR', 'France': 'EUR',
'Germany': 'EUR', 'Greece': 'EUR', 'Ireland': 'EUR', 'Italy': 'EUR', 'Kosovo': 'EUR', 'Latvia': 'EUR', 'Lithuania': 'EUR', 'Luxembourg': 'EUR',
'Malta': 'EUR', 'Montenegro': 'EUR', 'Monaco': 'EUR', 'Netherlands': 'EUR', 'Portugal': 'EUR', 'San Marino': 'EUR', 'Slovakia': 'EUR', 'Slovenia': 'EUR',
'Spain': 'EUR', 'Georgia': 'GEL', 'Hong Kong (China)': 'HKD', 'Hungary': 'HUF', 'Iceland': 'ISK', 'Israel': 'ILS', 'Japan': 'JPY', 'South Korea': 'KRW',
'Macau': 'MOP', 'Malaysia': 'MYR', 'Mexico': 'MXN', 'Moldova': 'MDL', 'New Zealand': 'NZD', 'North Macedonia': 'MKD', 'Norway': 'NOK', 'Oman': 'OMR',
'Poland': 'PLN', 'Qatar': 'QAR', 'Romania': 'RON', 'Russia': 'RUB', 'SAR': 'Saudi Arabia', 'Serbia': 'RSD', 'Singapore': 'SGD', 'Sweden': 'SEK',
'Taiwan': 'TWD', 'Thailand': 'THB', 'Turkey': 'TRY', 'Ukraine': 'UAH', 'United Kingdom': 'GBP', 'Gibraltar': 'GBP', 'Isle of Man': 'GBP',
'Jersey': 'GBP', 'Uruguay': 'UYU', 'United States': 'USD', 'Ecuador': 'USD', 'Paraguay': 'PYG', 'Argentina': 'USD'}

# Pyspark session to be used by each transformation function
pyspark = create_spark_session('col_api_etl')

def merge_cities_with_currencies(spark_session: SparkSession, country_abbreviation_combinations : list):
   # Retreive cities and currency_conversion_rates from S3 bucket
   cities = get_data('cities')
   currency_conversion_rates = get_data('currency_conversion_rates')

   

    



