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

def merge_locations_with_currencies(spark_session: SparkSession, country_abbreviation_combinations : list):
   # Retrieve locations and currency_conversion_rates from S3 bucket
   locations = get_data(file_prefix = 'locations.json')
   currency_conversion_rates = get_data(file_prefix = 'currency_conversion_rates')

   # Convert data into lists of Row objects
   locations_rows = [Row(**row) for row in locations]
   currency_conversion_rates_rows = [Row(**row) for row in currency_conversion_rates]

   # Create dataframes from row objects
   locations_df = pyspark.createDataFrame(locations_rows)
   currency_conversion_rates_df = pyspark.createDataFrame(currency_conversion_rates_rows)

   # Create map based on country_abbreviation_combinations
   country_abbreviation_combinations_map = functions.create_map(*[functions.lit(combination) for combination in chain(*country_abbreviation_combinations.items())])

   # Add Abbreviation column using country_abbreviation_combinations
   locations_df = locations_df.withColumn('Abbreviation', functions.when(functions.col('Country').isin(list(country_abbreviation_combinations.keys())), 
   country_abbreviation_combinations_map[functions.col('Country')]))

   # Remove commas from USD_to_local and converting to floating type
   currency_conversion_rates_df = currency_conversion_rates_df.withColumn('USD_to_local', functions.regexp_replace(functions.col('USD_to_local'), ',', '').cast(FloatType()))

   # Join dataframes
   locations_with_currencies_df = locations_df.join(currency_conversion_rates_df, 'Abbreviation', 'inner')

   # Convert to list of dictionaries
   locations_with_currencies = [{**row.asDict(), 'USD_to_local': round(row.USD_to_local, 2)} for row in locations_with_currencies_df.collect()]

   # Load data to S3 transformed bucket
   put_data(file_prefix = 'locations_with_currencies', data = locations_with_currencies, bucket_type = 'transformed')

def merge_and_transform(spark_session: SparkSession, include_livingcost: bool, items_to_filter_by: list, output_file: str):
   '''Only numbeo_price_info will be used if livingcost_price_info is not specified in files'''
   # Retrieve numbeo_price_info from S3 bucket
   numbeo_price_info = get_data(file_prefix = 'numbeo_price_info')

   # Convert data into list of Row objects
   numbeo_price_info_rows = [Row(**row) for row in numbeo_price_info]

   # Create dataframe from Row objects
   numbeo_price_info_df = pyspark.createDataFrame(numbeo_price_info_rows)

   # Filter items
   numbeo_price_info_df_filtered = numbeo_price_info_df.filter(functions.col('Item').isin(items_to_filter_by))

   # Format price string and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

   # Additional transformations if include_livingcost == True
   if include_livingcost == True:
      livingcost_price_info = get_data(file_prefix = 'livingcost_price_info')

      # Convert data into list of Row objects
      livingcost_price_info_rows = [Row(**row) for row in livingcost_price_info]

      # Create dataframe from Row objects
      livingcost_price_info_df = pyspark.createDataFrame(livingcost_price_info_rows)

      # Filter items
      livingcost_price_info_df_filtered = livingcost_price_info_df.filter(functions.col('Item').isin(items_to_filter_by))

      # Format price string and convert to float
      livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
      livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

      # Additional transformations required for foodbeverage output file
      if output_file == 'foodbeverage':
         restaurant_items = ['Dinner (2 People Mid Range Restaurant)', 'Lunch', 'Domestic Draught (0.5L)', 'Cappuccino (Regular)', 'Coke (0.5L)']
         beverage_items = ['Milk(1L)', 'Water(1L)', 'Wine (750ml Bottle Mid Range)', 'Domestic Beer (0.5L Bottle)', 'Cappuccino (Regular)',
         'Coke (0.5L)']
         numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Purchase Point', 
         functions.when(functions.col('Item').isin(restaurant_items), 'Restaurant').otherwise('Supermarket'))
         numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Item Category', 
         functions.when(functions.col('Item').isin(beverage_items), 'Beverage').otherwise('Food'))
         livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Purchase Point', 
         functions.when(functions.col('Item').isin(restaurant_items), 'Restaurant').otherwise('Supermarket'))
         livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Item Category', 
         functions.when(functions.col('Item').isin(beverage_items), 'Beverage').otherwise('Food'))

      # Join dataframes
      combined_price_info_df = numbeo_price_info_df_filtered.union(livingcost_price_info_df_filtered)

      # Convert to list of dictionaries
      combined_price_info = [{**row.asDict(), 'Price': round(row.Price, 2)} for row in combined_price_info_df.collect()]

      # Load data to S3 transformed bucket
      put_data(file_prefix = output_file, data = combined_price_info, bucket_type = 'transformed')
   
   else:
      # Convert to list of dictionaries
      price_info = [{**row.asDict(), 'Price': round(row.Price, 2)} for row in numbeo_price_info_df_filtered.collect()]

      # Load data to S3 transformed bucket
      put_data(file_prefix = output_file, data = price_info, bucket_type = 'transformed')

   








    



