from pyspark.sql import SparkSession, Row, functions
from typing import Union
from utils.aws_utils import *

# Creates spark session
def create_spark_session(app_name: str) -> SparkSession:
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    return spark

# Creates dataframe
def create_dataframe(spark_session : SparkSession, extract_source: str, items_to_filter_by: list) -> Union[SparkSession , Exception]:
    '''extract_source must be either "numbeo_price_info" or "livingcost_price_info"'''
    if extract_source == 'numbeo_price_info' or extract_source == 'livingcost_price_info':
        price_info = get_data(file_prefix=extract_source)

        # Convert data into list of Row objects
        price_info_rows = [Row(**row) for row in price_info]

        # Create dataframe from Row objects
        price_info_df = spark_session.createDataFrame(price_info_rows)

        # Filter items
        price_info_df_filtered = price_info_df.filter(functions.col('Item').isin(items_to_filter_by))

        # Return filtered dataframe
        return price_info_df_filtered
    else:
        raise Exception('extract source must be either "numbeo_price_info" or "livingcost_price_info"')
