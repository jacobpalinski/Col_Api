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

with DAG(dag_id = 'col_api_etl', default_args = default_args, schedule_interval = timedelta(7), catchup = False) as dag:
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
    # pyspark.py merge + transformation functions
    merge_locations_with_currencies = PythonOperator(
        task_id = 'merge_locations_with_currencies',
        python_callable = merge_locations_with_currencies,
        op_kwargs = {'spark_session': pyspark}
    )
    merge_and_transform_homepurchase = PythonOperator(
        task_id = 'merge_and_transform_homepurchase',
        python_callable = merge_and_transform_homepurchase,
        op_kwargs = {'spark_session': pyspark}
    )
    merge_and_transform_foodbeverage = PythonOperator(
        task_id = 'merge_and_transform_foodbeverage',
        python_callable = merge_and_transform_foodbeverage,
        op_kwargs = {'spark_session': pyspark}
    )
    merge_and_transform_utilities = PythonOperator(
        task_id = 'merge_and_transform_utilities',
        python_callable = merge_and_transform_utilities,
        op_kwargs = {'spark_session': pyspark}
    )
    merge_and_transform_rent = PythonOperator(
        task_id = 'merge_and_transform_rent',
        python_callable = merge_and_transform_rent,
        op_kwargs = {'spark_session': pyspark}
    )
    merge_and_transform_transportation = PythonOperator(
        task_id = 'merge_and_transform_transportation',
        python_callable = merge_and_transform_transportation,
        op_kwargs = {'spark_session': pyspark}
    )
    merge_and_transform_apparel = PythonOperator(
        task_id = 'merge_and_transform_apparel',
        python_callable = merge_and_transform_apparel,
        op_kwargs = {'spark_session': pyspark}
    )
    merge_and_transform_childcare = PythonOperator(
        task_id = 'merge_and_transform_childcare',
        python_callable = merge_and_transform_childcare,
        op_kwargs = {'spark_session': pyspark}
    )
    merge_and_transform_leisure = PythonOperator(
        task_id = 'merge_and_transform_leisure',
        python_callable = merge_and_transform_leisure,
        op_kwargs = {'spark_session': pyspark}
    )
    extract_currency_conversion_rates >> [extract_numbeo_prices_from_city, extract_livingcost_prices_from_city] \
    >> merge_locations_with_currencies >> merge_and_transform_homepurchase >> merge_and_transform_foodbeverage \
    >> merge_and_transform_utilities >> merge_and_transform_rent >> merge_and_transform_transportation >> merge_and_transform_apparel \
    >> merge_and_transform_childcare >> merge_and_transform_leisure
    

    