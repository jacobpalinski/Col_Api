import boto3
from pyspark.sql import SparkSession, Row, functions
from pyspark.sql.types import FloatType, StringType
from itertools import chain
from utils.spark_utils import create_spark_session
from utils.aws_utils import *

country_abbreviation_combinations = {'United Arab Emirates': 'AED', 'Australia': 'AUD', 'Bosnia and Herzegovina': 'BAM', 'Bahrain': 'BHD', 
'Bulgaria': 'BGN', 'Brazil': 'BYN', 'Canada': 'CAD', 'Switzerland': 'CHF','Liechtenstein': 'CHF', 'Chile': 'CLP', 'China': 'CNY', 'Colombia': 'COP', 
'Costa Rica': 'CRC', 'Czech Republic': 'CZK', 'Denmark': 'DKK', 'Andorra': 'EUR', 'Austria': 'EUR', 'Belgium': 'EUR', 'Croatia': 'EUR', 'Cyprus': 'EUR', 
'Estonia': 'EUR', 'Finland': 'EUR', 'France': 'EUR','Germany': 'EUR', 'Greece': 'EUR', 'Ireland': 'EUR', 'Italy': 'EUR', 'Latvia': 'EUR', 
'Lithuania': 'EUR', 'Luxembourg': 'EUR', 'Malta': 'EUR', 'Montenegro': 'EUR', 'Monaco': 'EUR', 'Netherlands': 'EUR', 'Portugal': 'EUR', 'San Marino': 'EUR', 
'Slovakia': 'EUR', 'Slovenia': 'EUR', 'Spain': 'EUR', 'Georgia': 'GEL', 'Hong Kong': 'HKD', 'Hungary': 'HUF', 'Israel': 'ILS', 'Iceland': 'ISK', 
'Japan': 'JPY', 'South Korea': 'KRW', 'Kuwait': 'KWD', 'Macau': 'MOP', 'Malaysia': 'MYR', 'Mexico': 'MXN', 'New Zealand': 'NZD', 'Norway': 'NOK', 'Oman': 'OMR',
'Poland': 'PLN', 'Qatar': 'QAR', 'Romania': 'RON', 'Russia': 'RUB', 'Saudi Arabia': 'SAR', 'Serbia': 'RSD', 'Singapore': 'SGD', 'Sweden': 'SEK',
'Taiwan': 'TWD', 'Thailand': 'THB', 'Turkey': 'TRY', 'Ukraine': 'UAH', 'United Kingdom': 'GBP','Uruguay': 'UYU', 'United States': 'USD', 'Ecuador': 'USD', 
'Paraguay': 'PYG', 'Panama': 'USD', 'Argentina': 'USD'}

# Pyspark session to be used by each transformation function
pyspark = create_spark_session('col_api_etl')

def merge_cities_with_currencies(spark_session: SparkSession, country_abbreviation_combinations : list):
   # Retreive cities and currency_conversion_rates from S3 bucket
   cities = get_data('cities')
   currency_conversion_rates = get_data('currency_conversion_rates')

   # Convert data into lists of Row objects
   cities_rows = [Row(**row) for row in cities]
   currency_conversion_rates_rows = [Row(**row) for row in currency_conversion_rates]

   # Create dataframes from row objects
   cities_df = pyspark.createDataFrame(cities_rows)
   currency_conversion_rates_df = pyspark.createDataFrame(currency_conversion_rates_rows)

   # Dictionary used to replace countries with None in City column in cities_df
   country_capital_dict = {'Bahrain': 'Manama', 'Liechtenstein': 'Vaduz', 'Chile': 'Santiago', 'Costa Rica': 'San Jose', 'Andorra': 'Andorra la Vella', 'Estonia': 'Tallinn',
   'Latvia': 'Riga', 'Luxembourg': 'Luxembourg','Malta': 'Valletta', 'Montenegro': 'Podgorica', 'Monaco': 'Monaco', 'San Marino': 'San Marino', 'Slovakia': 'Bratislava', 
   'Slovenia': 'Ljubljana', 'Georgia':'Tbilisi', 'Hong Kong': 'Hong Kong', 'Iceland': 'Reykjavik', 'Kuwait': 'Kuwait City', 'Macau': 'Macau' ,'Oman': 'Muscat', 'Qatar': 'Doha', 
   'Singapore': 'Singapore', 'Uruguay': 'Montevideo', 'Paraguay': 'Asuncion', 'Panama': 'Panama City', 'Argentina': 'Buenos Aires'}

   # UDF to replace 'City' based on 'Country' using country_capital_dict
   def replace_city(country, city):
      return country_capital_dict.get(country, city)
   
   # Register the UDF
   replace_city_udf = functions.udf(replace_city, StringType())

   # Replace rows with None City column with country_capital_dict
   cities_df = cities_df.withColumn('City', replace_city_udf(functions.col('Country'), functions.col('City')))

   # Create map based on country_abbreviation_combinations
   country_abbreviation_combinations_map = functions.create_map(*[functions.lit(combination) for combination in chain(*country_abbreviation_combinations.items())])

   # Add Abbreviation column using country_abbreviation_combinations
   cities_df = cities_df.withColumn('Abbreviation', functions.when(functions.col('Country').isin(list(country_abbreviation_combinations.keys())), 
   country_abbreviation_combinations_map[functions.col('Country')]))

   # Remove commas from USD_to_local and converting to floating type
   currency_conversion_rates_df = currency_conversion_rates_df.withColumn('USD_to_local', functions.regexp_replace(functions.col('USD_to_local'), ',', '').cast(FloatType()))

   # Join dataframes
   cities_with_currencies_df = cities_df.join(currency_conversion_rates_df, 'Abbreviation', 'inner')

   # Convert to list of dictionaries
   cities_with_currencies = [{**row.asDict(), 'USD_to_local': round(row.USD_to_local, 2)} for row in cities_with_currencies_df.collect()]

   # Load data to S3 transformed bucket
   put_data(file_prefix = 'cities_with_currencies', data = cities_with_currencies, bucket_type = 'transformed')


    



