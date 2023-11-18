import boto3
from pyspark.sql import SparkSession, Row, functions
from pyspark.sql.types import FloatType, StringType
from itertools import chain
from utils.spark_utils import *
from utils.aws_utils import *

# Pyspark session to be used by each transformation function
pyspark = create_spark_session('col_api_etl')

# Merge locations.json with currency_conversion_rates file
def merge_locations_with_currencies(spark_session: SparkSession):
   # Dictionary to match currency abbreviation with relevant country
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

   # Retrieve locations and currency_conversion_rates from S3 bucket
   locations = get_data(file_prefix = 'locations.json')
   currency_conversion_rates = get_data(file_prefix = 'currency_conversion_rates')

   # Convert data into lists of Row objects
   locations_rows = [Row(**row) for row in locations]
   currency_conversion_rates_rows = [Row(**row) for row in currency_conversion_rates]

   # Create dataframes from row objects
   locations_df = spark_session.createDataFrame(locations_rows)
   currency_conversion_rates_df = spark_session.createDataFrame(currency_conversion_rates_rows)

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

# Merge and transform home purchase items
def merge_and_transform_homepurchase(spark_session : SparkSession):
   # Create base filtered dataframe
   numbeo_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'numbeo_price_info',
   items_to_filter_by = ['Price per Square Meter to Buy Apartment in City Centre', 'Price per Square Meter to Buy Apartment Outside of Centre', 
   'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)'])

   # Create seperate dataframe for 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)' rate values
   mortgage_interest_df = numbeo_price_info_df_filtered.filter(functions.col('Item') == 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)')

   # Remove rows from numbeo_price_info_df_filtered that have 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)' as value for 'Item' Column
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.filter(functions.col('Item') != 'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)')

   # Create 'Property Location' column
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Property Location', 
   functions.when(functions.col('Item').contains('City Centre'), 'City Centre').otherwise('Outside City Centre'))
   
   # Create 'Price per Square Meter' column
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price per Square Meter', functions.col('Price'))

   # Format 'Price per Square Meter' column and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price per Square Meter', functions.regexp_replace(functions.col('Price per Square Meter'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price per Square Meter', functions.col('Price per Square Meter').cast('float'))

   # Remove 'Item' and 'Price' columns
   columns_to_include = ['City', 'Property Location', 'Price per Square Meter']
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.select(columns_to_include)

   # Format 'Price' column and convert to float
   mortgage_interest_df = mortgage_interest_df.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   mortgage_interest_df = mortgage_interest_df.withColumn('Price', functions.col('Price').cast('float'))

   # Only keep 'City' and 'Price' columns from mortgage_interest_df when joining with numbeo_price_info_df_filtered
   columns_to_include = ['City', 'Price']
   mortgage_interest_df= mortgage_interest_df.select(columns_to_include)

   # Join
   joined_df = numbeo_price_info_df_filtered.join(mortgage_interest_df, on = 'City', how = 'inner')

   # Rename 'Price' to 'Mortgage Interest'
   joined_df = joined_df.withColumnRenamed('Price', 'Mortgage Interest')

   # Convert to list of dictionaries
   joined_dict = [{**row.asDict(), 'Price per Square Meter': round(row['Price per Square Meter'], 2), 
   'Mortgage Interest': round(row['Mortgage Interest'], 2)} for row in joined_df.collect()]

   # Put in S3 bucket
   put_data(file_prefix = 'homepurchase', data = joined_dict, bucket_type = 'transformed')

# Merge and transfrom rent items
def merge_and_transform_rent(spark_session: SparkSession):
   # Create base filtered dataframe
   numbeo_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'numbeo_price_info',
   items_to_filter_by = ['Rent 1 Bedroom Apartment City Centre', 'Rent 1 Bedroom Apartment Outside City Centre',
   'Rent 3 Bedroom Apartment City Centre', 'Rent 3 Bedroom Apartment Outside City Centre'])

   # Create 'Property Location' column
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Property Location', 
   functions.when(functions.col('Item').contains('Outside City Centre'), 'Outside City Centre').otherwise('City Centre'))

   # Create 'Bedrooms' column
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Bedrooms', functions.when(functions.col('Item').contains('3'), '3').otherwise('1'))

   # Convert 'Bedrooms' column to int
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Bedrooms', functions.col('Bedrooms').cast('int'))

   # Format 'Price' column and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

   # Rename 'Price' column to 'Monthly Price'
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumnRenamed('Price', 'Monthly Price')

   # Remove 'Item' column
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.select([column for column in numbeo_price_info_df_filtered.columns if column != 'Item'])

   # Convert to list of dictionaries
   numbeo_price_info = [{**row.asDict(), 'Monthly Price': round(row['Monthly Price'], 2)} for row in numbeo_price_info_df_filtered.collect()]

   # Put in S3 bucket
   put_data(file_prefix = 'rent', data = numbeo_price_info, bucket_type = 'transformed')

# Merge and transfrom foodbeverage items
def merge_and_transform_foodbeverage(spark_session: SparkSession):
   # Create base dataframes
   numbeo_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'numbeo_price_info',
   items_to_filter_by = ['Milk (1L)', 'Bread (500g)', 'Rice (1kg)', 'Eggs (x12)', 'Cheese (1kg)', 'Chicken Fillets (1kg)', 'Beef Round (1kg)', 'Apples (1kg)', 'Banana (1kg)',
   'Oranges (1kg)', 'Tomato (1kg)', 'Potato (1kg)', 'Onion (1kg)', 'Lettuce (1 Head)', 'Water (1L)', 'Wine (750ml Bottle Mid Range)',
   'Domestic Beer (0.5L Bottle)', 'Cigarettes (20 Pack Malboro)', 'Dinner (2 People Mid Range Restaurant)', 'Lunch', 'Domestic Draught (0.5L)',
   'Cappuccino (Regular)', 'Coke (0.5L)'])
   livingcost_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'livingcost_price_info',
   items_to_filter_by = ['Milk (1L)', 'Bread (500g)', 'Rice (1kg)', 'Eggs (x12)', 'Cheese (1kg)', 'Chicken Fillets (1kg)', 'Beef Round (1kg)', 'Apples (1kg)', 'Banana (1kg)',
   'Oranges (1kg)', 'Tomato (1kg)', 'Potato (1kg)', 'Onion (1kg)', 'Lettuce (1 Head)', 'Water (1L)', 'Wine (750ml Bottle Mid Range)',
   'Domestic Beer (0.5L Bottle)', 'Cigarettes (20 Pack Malboro)', 'Dinner (2 People Mid Range Restaurant)', 'Lunch', 'Domestic Draught (0.5L)',
   'Cappuccino (Regular)', 'Coke (0.5L)'])

   # Format 'Price' column in each dataframe and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

   # Filter restuarant and beverage items
   restaurant_items = ['Dinner (2 People Mid Range Restaurant)', 'Lunch', 'Domestic Draught (0.5L)', 'Cappuccino (Regular)', 'Coke (0.5L)']
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Purchase Point', 
   functions.when(functions.col('Item').isin(restaurant_items), 'Restaurant').otherwise('Supermarket'))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Purchase Point', 
   functions.when(functions.col('Item').isin(restaurant_items), 'Restaurant').otherwise('Supermarket'))

   beverage_items = ['Milk (1L)', 'Water (1L)', 'Wine (750ml Bottle Mid Range)', 'Domestic Beer (0.5L Bottle)', 'Cappuccino (Regular)',
   'Coke (0.5L)', 'Domestic Draught (0.5L)']
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Item Category', 
   functions.when(functions.col('Item').isin(beverage_items), 'Beverage').otherwise('Food'))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Item Category', 
   functions.when(functions.col('Item').isin(beverage_items), 'Beverage').otherwise('Food'))

   # Combine dataframes into single dataframe
   combined_price_info_df = numbeo_price_info_df_filtered.union(livingcost_price_info_df_filtered)

   # Convert to list of dictionaries
   combined_price_info = [{**row.asDict(), 'Price': round(row.Price, 2)} for row in combined_price_info_df.collect()]

   # Load data to S3 transformed bucket
   put_data(file_prefix = 'foodbeverage', data = combined_price_info, bucket_type = 'transformed')

# Merge and transfrom utilities items
def merge_and_transform_utilities(spark_session: SparkSession):
   # Create base dataframes
   numbeo_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'numbeo_price_info',
   items_to_filter_by = ['Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Electricity, Heating, Cooling, Water and Garbage (Family)',
   'Internet (60 Mbps, Unlimited Data, Monthly)', 'Mobile Plan (10GB+ Data, Monthly)'])
   livingcost_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'livingcost_price_info',
   items_to_filter_by = ['Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Electricity, Heating, Cooling, Water and Garbage (Family)',
   'Internet (60 Mbps, Unlimited Data, Monthly)', 'Mobile Plan (10GB+ Data, Monthly)'])

   # Format 'Price' column in each dataframe and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

   # Rename 'Price' column to 'Monthly Price'
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumnRenamed('Price', 'Monthly Price')
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumnRenamed('Price', 'Monthly Price')

   # Rename 'Item' column to 'Utility'
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumnRenamed('Item', 'Utility')
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumnRenamed('Item', 'Utility')

   # Combine dataframes into single dataframe
   combined_price_info_df = numbeo_price_info_df_filtered.union(livingcost_price_info_df_filtered)

   # Convert to list of dictionaries
   combined_price_info = [{**row.asDict(), 'Monthly Price': round(row['Monthly Price'], 2)} for row in combined_price_info_df.collect()]

   # Load data to S3 transformed bucket
   put_data(file_prefix = 'utilities', data = combined_price_info, bucket_type = 'transformed')

# Merge and transfrom transportation items
def merge_and_transform_transportation(spark_session: SparkSession):
   # Create base dataframes
   numbeo_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'numbeo_price_info',
   items_to_filter_by = ['Public Transport (One Way Ticket)', 'Public Transport (Monthly)', 'Petrol (1L)', 'Taxi (8km)'])
   livingcost_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'livingcost_price_info',
   items_to_filter_by = ['Public Transport (One Way Ticket)', 'Public Transport (Monthly)', 'Petrol (1L)', 'Taxi (8km)'])

   # Format 'Price' column in each dataframe and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

   # Rename 'Item' column to 'Type'
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumnRenamed('Item', 'Type')
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumnRenamed('Item', 'Type')

   # Combine dataframes into single dataframe
   combined_price_info_df = numbeo_price_info_df_filtered.union(livingcost_price_info_df_filtered)

   # Convert to list of dictionaries
   combined_price_info = [{**row.asDict(), 'Price': round(row['Price'], 2)} for row in combined_price_info_df.collect()]

   # Load data to S3 transformed bucket
   put_data(file_prefix = 'transportation', data = combined_price_info, bucket_type = 'transformed')

# Merge and transform childcare items
def merge_and_transform_childcare(spark_session: SparkSession):
   # Create base dataframe
   numbeo_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'numbeo_price_info',
   items_to_filter_by = ['Daycare / Preschool (1 Month)', 'International Primary School (1 Year)'])

   # Format 'Price' column in dataframe and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

   # Rename Daycare / Preschool (1 Month) item and annualise price
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Item', functions.when(functions.col('Item') == 'Daycare / Preschool (1 Month)', 'Daycare / Preschool (1 Year)').otherwise(functions.col('Item')))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.when(functions.col('Item') == 'Daycare / Preschool (1 Year)', functions.col('Price') * 12).otherwise(functions.col('Price')))

   # Rename 'Price' column to 'Annual Price'
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumnRenamed('Price', 'Annual Price')

   # Rename 'Item' column to 'Type'
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumnRenamed('Item', 'Type')

   # Convert to list of dictionaries
   numbeo_price_info = [{**row.asDict(), 'Annual Price': round(row['Annual Price'], 2)} for row in numbeo_price_info_df_filtered.collect()]

   # Load data to S3 transformed bucket
   put_data(file_prefix = 'childcare', data = numbeo_price_info, bucket_type = 'transformed')

# Merge and transfrom apparel items
def merge_and_transform_apparel(spark_session: SparkSession):
   # Create base dataframes
   numbeo_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'numbeo_price_info',
   items_to_filter_by = ['Pair of Jeans', 'Summer Dress Chain Store', 'Mens Leather Business Shoes', 'Brand Sneakers'])
   livingcost_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'livingcost_price_info',
   items_to_filter_by = ['Pair of Jeans', 'Summer Dress Chain Store', 'Mens Leather Business Shoes', 'Brand Sneakers'])

   # Format 'Price' column in each dataframe and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   livingcost_price_info_df_filtered = livingcost_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

   # Combine dataframes into single dataframe
   combined_price_info_df = numbeo_price_info_df_filtered.union(livingcost_price_info_df_filtered)

   # Convert to list of dictionaries
   combined_price_info = [{**row.asDict(), 'Price': round(row['Price'], 2)} for row in combined_price_info_df.collect()]

   # Load data to S3 transformed bucket
   put_data(file_prefix = 'apparel', data = combined_price_info, bucket_type = 'transformed')

# Merge and transfrom leisure items
def merge_and_transform_leisure(spark_session: SparkSession):
   # Create base dataframe
   numbeo_price_info_df_filtered = create_dataframe(spark_session = spark_session, extract_source = 'numbeo_price_info',
   items_to_filter_by = ['Gym Membership (Monthly)', 'Tennis Court Rent (1hr)', 'Cinema International Release'])

   # Format 'Price' column in dataframe and convert to float
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.regexp_replace(functions.col('Price'), r'[^0-9.]', ''))
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumn('Price', functions.col('Price').cast('float'))

   # Rename 'Item' column to 'Activity'
   numbeo_price_info_df_filtered = numbeo_price_info_df_filtered.withColumnRenamed('Item', 'Activity')

   # Convert to list of dictionaries
   numbeo_price_info = [{**row.asDict(), 'Price': round(row['Price'], 2)} for row in numbeo_price_info_df_filtered.collect()]

   # Load data to S3 transformed bucket
   put_data(file_prefix = 'leisure', data = numbeo_price_info, bucket_type = 'transformed')



   








    



