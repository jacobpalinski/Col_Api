import pytest
from utils.aws_utils import *
from utils.spark_utils import *
from tests.fixtures.fixtures_testing import current_date, mock_environment_variables, mock_boto3_s3

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
        mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'cities{current_date}', Body = json.dumps(input_data))
    elif bucket_type == 'transformed':
        mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'cities{current_date}', Body = json.dumps(input_data))

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