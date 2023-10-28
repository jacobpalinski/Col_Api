from datetime import timedelta, datetime
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from scripts.extraction_py import *
from scripts.pyspark import *
from scripts.aws_utils import *
from scripts.spark_utils import *

default_args = {
    'owner': 'airflow',
    'start_date': pendulum.today(),
    'retries': 1,
    'retry_delay': timedelta(seconds = 30)
}

with DAG(dag_id = 'Col_Api_DAG', default_args = default_args, schedule_interval = timedelta(1), catchup = False) as dag:
    pass