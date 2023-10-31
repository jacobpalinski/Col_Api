import pytest
from utils.aws_utils import *
from utils.spark_utils import *
from tests.fixtures.fixtures_testing import current_date, mock_environment_variables, mock_boto3_s3, pyspark_session

@pytest.mark.parametrize('file_prefix', ['locations.json', 'currency_conversion_rates'])
def test_get_data(mock_environment_variables, mock_boto3_s3, current_date, file_prefix):
    data = get_data(file_prefix = file_prefix)
    if file_prefix == 'locations.json':
        mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'locations.json')
        assert data == [{'Country': 'Australia', 'City': 'Perth'},{'Country': 'New Zealand', 'City': 'Auckland'}, 
        {'Country': 'Hong Kong', 'City': 'Hong Kong'}, {'Country': 'Paraguay', 'City': 'Asuncion'}]
    else:
        mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'currency_conversion_rates{current_date}')
        assert data == [{'Abbreviation': 'AUD', 'USD_to_local': '1.55'},{'Abbreviation': 'NZD', 'USD_to_local': '1.69'},
        {'Abbreviation': 'SGD', 'USD_to_local': '1.36'}, {'Abbreviation': 'PYG', 'USD_to_local': '7,258.93'}]

@pytest.mark.parametrize('bucket_type', ['raw','transformed'])
def test_put_data_valid_bucket(mock_environment_variables, mock_boto3_s3, current_date, bucket_type):
    current_date = datetime.date.today().strftime('%Y%m%d')
    input_data = ['Perth']
    put_data(file_prefix = 'cities', data = input_data, bucket_type = bucket_type)
    if bucket_type == 'raw':
        mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'cities{current_date}', Body = json.dumps(input_data), ContentType = 'application/json')
    elif bucket_type == 'transformed':
        mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'cities{current_date}', Body = json.dumps(input_data), ContentType = 'application/json')

def test_put_data_invalid_bucket(mock_environment_variables, mock_boto3_s3, current_date):
    current_date = datetime.date.today().strftime('%Y%m%d')
    input_data = ['Perth']
    with pytest.raises(Exception) as exc_info:
        put_data(file_prefix = 'cities', data = input_data, bucket_type = 'invalid')
    assert str(exc_info.value) == 'bucket_type must be either "raw" or "transformed"'

def test_create_spark_session():
    app_name = 'test_spark_session'
    session = create_spark_session(app_name)
    assert isinstance(session, SparkSession)

@pytest.mark.parametrize('extract_source', ['numbeo_price_info', 'livingcost_price_info'])
def test_create_dataframe(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date, extract_source):
    if extract_source == 'numbeo_price_info':
        df = create_dataframe(spark_session = pyspark_session, extract_source = 'numbeo_price_info', 
        items_to_filter_by = ['Price per Square Meter to Buy Apartment in City Centre', 'Price per Square Meter to Buy Apartment Outside of Centre', 
        'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)'])
         # Check row count
        assert df.count() == 8
        # Check schema
        assert df.columns == ['City', 'Item', 'Price']
        # Check data
        assert df.collect() == [('Perth', 'Price per Square Meter to Buy Apartment in City Centre', '6,741.52\u00a0$'),
        ('Perth', 'Price per Square Meter to Buy Apartment Outside of Centre', '5,395.77\u00a0$'),
        ('Auckland', 'Price per Square Meter to Buy Apartment in City Centre', '9,155.42\u00a0$'),
        ('Auckland', 'Price per Square Meter to Buy Apartment Outside of Centre', '8,089.96\u00a0$'),
        ('Hong Kong', 'Price per Square Meter to Buy Apartment in City Centre', '30,603.04\u00a0$'),
        ('Hong Kong', 'Price per Square Meter to Buy Apartment Outside of Centre', '20,253.04\u00a0$'),
        ('Asuncion', 'Price per Square Meter to Buy Apartment in City Centre', '1,118.53\u00a0$'),
        ('Asuncion', 'Price per Square Meter to Buy Apartment Outside of Centre', '933.23\u00a0$')]
        mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
    else:
        df = create_dataframe(spark_session = pyspark_session, extract_source = 'livingcost_price_info', 
        items_to_filter_by = ['Electricity, Heating, Cooling, Water and Garbage (1 Person)', 'Electricity, Heating, Cooling, Water and Garbage (Family)',
        'Internet (60 Mbps, Unlimited Data, Monthly)', 'Mobile Plan (10GB+ Data, Monthly)'])
        # Check row count
        assert df.count() == 8
        # Check schema
        assert df.columns == ['City', 'Item', 'Price']
        # Check data
        assert df.collect() == [('Perth', 'Electricity, Heating, Cooling, Water and Garbage (1 Person)', '$124'), 
        ('Perth', "Electricity, Heating, Cooling, Water and Garbage (Family)", '$216'), 
        ("Auckland", "Electricity, Heating, Cooling, Water and Garbage (1 Person)", '$96.1'), 
        ("Auckland", "Electricity, Heating, Cooling, Water and Garbage (Family)", '$148'), 
        ("Hong Kong", "Electricity, Heating, Cooling, Water and Garbage (1 Person)", '$146'), 
        ("Hong Kong", "Electricity, Heating, Cooling, Water and Garbage (Family)", '$223'), 
        ("Asuncion", "Electricity, Heating, Cooling, Water and Garbage (1 Person)", '$39.3'), 
        ("Asuncion", "Electricity, Heating, Cooling, Water and Garbage (Family)", '$61.3')]
        mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'livingcost_price_info{current_date}')

def test_create_dataframe_invalid_extract_source(mock_environment_variables, mock_boto3_s3, pyspark_session, current_date):
    with pytest.raises(Exception) as exc_info:
        df = create_dataframe(spark_session = pyspark_session, extract_source = 'invalid_price_info', 
        items_to_filter_by = ['Price per Square Meter to Buy Apartment in City Centre', 'Price per Square Meter to Buy Apartment Outside of Centre', 
        'Mortgage Interest Rate (Annual, 20 Years Fixed-Rate)'])
        # Check row count
        assert df.count() == 8
        # Check schema
        assert df.columns == ['City', 'Item', 'Price']
        # Check data
        assert df.collect() == [('Perth', 'Price per Square Meter to Buy Apartment in City Centre', '6,741.52\u00a0$'),
        ('Perth', 'Price per Square Meter to Buy Apartment Outside of Centre', '5,395.77\u00a0$'),
        ('Auckland', 'Price per Square Meter to Buy Apartment in City Centre', '9,155.42\u00a0$'),
        ('Auckland', 'Price per Square Meter to Buy Apartment Outside of Centre', '8,089.96\u00a0$'),
        ('Hong Kong', 'Price per Square Meter to Buy Apartment in City Centre', '30,603.04\u00a0$'),
        ('Hong Kong', 'Price per Square Meter to Buy Apartment Outside of Centre', '20,253.04\u00a0$'),
        ('Asuncion', 'Price per Square Meter to Buy Apartment in City Centre', '1,118.53\u00a0$'),
        ('Asuncion', 'Price per Square Meter to Buy Apartment Outside of Centre', '933.23\u00a0$')]
        mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'numbeo_price_info{current_date}')
    assert str(exc_info.value) == 'extract source must be either "numbeo_price_info" or "livingcost_price_info"'
    

