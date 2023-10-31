from datetime import timedelta, datetime
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from scripts.extraction import *
from scripts.pyspark import *

default_args = {
    'owner': 'airflow',
    'start_date': pendulum.today(),
    'retries': 1,
    'retry_delay': timedelta(seconds = 30)
}

with DAG(dag_id = 'col_api_etl', default_args = default_args, schedule_interval = timedelta(1), catchup = False) as dag:
    # Functions from extraction.py
    extract_currency_conversion_rates = PythonOperator(
        task_id = 'extract_currency_conversion_rates',
        python_callable = extract_currency_conversion_rates)
    extract_numbeo_prices_from_city = PythonOperator(
        task_id = 'extract_numbeo_prices_from_city',
        python_callable = extract_numbeo_prices_from_city
    )
    extract_livingcost_prices_from_city = PythonOperator(
        task_id = 'extract_livingcost_prices_from_city',
        python_callable = extract_livingcost_prices_from_city
    )
    # Pyspark merge + transformation functions
    merge_locations_with_currencies = PythonOperator(
        task_id = 'merge_locations_with_currencies',
        python_callable = merge_locations_with_currencies,
        op_kwargs = {'spark_session': pyspark, 'country_abbreviations_combinations': country_abbreviation_combinations}
    )
    merge_and_transform_homepurchase = PythonOperator(
        task_id = 'merge_and_transform_homepurchase',
        python_callable = merge_and_transform,
        op_kwargs = {'spark_session': pyspark, 'include_livingcost': False, 
        'items_to_filter_by': ['Price per Square Meter to Buy Apartment in City Centre', 'Price per Square Meter to Buy Apartment Outside of Centre'],
        'output_file': 'homepurchase'}
    )
    merge_and_transform_foodbeverage = PythonOperator(
        task_id = 'merge_and_transform_foodbeverage',
        python_callable = merge_and_transform,
        op_kwargs = {'spark_session': pyspark, 'include_livingcost': True, 
        'items_to_filter_by': ['Milk (1L)', 'Bread (500g)', 'Rice (1kg)', 'Eggs (x12)', 'Cheese (1kg)', 'Chicken Fillets (1kg)', 'Beef Round (1kg)', 'Apples (1kg)', 'Banana (1kg)',
        'Oranges (1kg)', 'Tomato (1kg)', 'Potato (1kg)', 'Onion (1kg)', 'Lettuce (1 Head)', 'Water (1L)', 'Wine (750ml Bottle Mid Range)',
        'Domestic Beer (0.5L Bottle)', 'Cigarettes (20 Pack Malboro)', 'Dinner (2 People Mid Range Restaurant)', 'Lunch', 'Domestic Draught (0.5L)',
        'Cappuccino (Regular)', 'Coke (0.5L)'], 'output_file': 'foodbeverage'}
    )
    merge_and_transform_utilities = PythonOperator(
        task_id = 'merge_and_transform_utilities',
        python_callable = merge_and_transform,
        op_kwargs = {'spark_session': pyspark, 'include_livingcost': True, 
        'items_to_filter_by': ['Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Electricity, Heating, Cooling, Water and Garbage (Family)',
        'Internet (60 Mbps, Unlimited Data, Monthly)', 'Mobile Plan (10GB+ Data, Monthly)'], 'output_file': 'utilities'}
    )
    merge_and_transform_rent = PythonOperator(
        task_id = 'merge_and_transform_rent',
        python_callable = merge_and_transform,
        op_kwargs = {'spark_session': pyspark, 'include_livingcost': False, 
        'items_to_filter_by': ['Rent 1 Bedroom Apartment City Centre', 'Rent 1 Bedroom Apartment Outside City Centre',
        'Rent 3 Bedroom Apartment City Centre', 'Rent 3 Bedroom Apartment Outside City Centre'], 'output_file': 'rent'}
    )
    merge_and_transform_transportation = PythonOperator(
        task_id = 'merge_and_transform_transportation',
        python_callable = merge_and_transform,
        op_kwargs = {'spark_session': pyspark, 'include_livingcost': True, 
        'items_to_filter_by': ['Public Transport (One Way Ticket)', 'Public Transport (Monthly)', 'Petrol (1L)', 'Taxi (8km)'], 'output_file': 'transportation'}
    )
    merge_and_transform_apparel = PythonOperator(
        task_id = 'merge_and_transform_apparel',
        python_callable = merge_and_transform,
        op_kwargs = {'spark_session': pyspark, 'include_livingcost': True, 
        'items_to_filter_by': ['Pair of Jeans', 'Summer Dress Chain Store', 'Mens Leather Business Shoes', 'Brand Sneakers'], 'output_file': 'apparel'}
    )
    merge_and_transform_childcare = PythonOperator(
        task_id = 'merge_and_transform_childcare',
        python_callable = merge_and_transform,
        op_kwargs = {'spark_session': pyspark, 'include_livingcost': False, 
        'items_to_filter_by': ['Daycare / Preschool (1 Month)', 'International Primary School (1 Year)'], 'output_file': 'childcare'}
    )
    merge_and_transform_leisure = PythonOperator(
        task_id = 'merge_and_transform_leisure',
        python_callable = merge_and_transform,
        op_kwargs = {'spark_session': pyspark, 'include_livingcost': False, 
        'items_to_filter_by': ['Gym Membership (Monthly)', 'Tennis Court Rent (1hr)', 'Cinema International Release'], 'output_file': 'leisure'}
    )
    extract_currency_conversion_rates >> extract_numbeo_prices_from_city >> extract_livingcost_prices_from_city \
    >> [merge_locations_with_currencies, merge_and_transform_homepurchase, merge_and_transform_foodbeverage,
    merge_and_transform_utilities, merge_and_transform_rent, merge_and_transform_transportation, merge_and_transform_apparel,
    merge_and_transform_childcare, merge_and_transform_leisure]
    

    