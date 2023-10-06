import pytest
from utils.aws_utils import *
from utils.spark_utils import *
from tests.fixtures.fixtures_testing import mock_environment_variables, mock_boto3_s3

def test_get_data(mock_environment_variables, mock_boto3_s3):
    current_date = datetime.date.today().strftime('%Y%m%d')
    data = get_data(file_prefix = 'cities')
    mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'cities{current_date}')
    assert data == [{'Australia': 'Perth'}]

def test_put_data(mock_environment_variables, mock_boto3_s3):
    current_date = datetime.date.today().strftime('%Y%m%d')
    put_data(file_prefix = 'cities', data = ['Perth'])
    mock_boto3_s3.put_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'cities{current_date}', Body = json.dumps(['Perth']))

def test_create_spark_session():
    app_name = 'test_spark_session'
    session = create_spark_session(app_name)
    assert isinstance(session, SparkSession)