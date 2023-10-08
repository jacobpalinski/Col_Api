import pytest
from utils.aws_utils import *
from utils.spark_utils import *
from tests.fixtures.fixtures_testing import current_date, mock_environment_variables, mock_boto3_s3

def test_get_data(mock_environment_variables, mock_boto3_s3, current_date):
    data = get_data(file_prefix = 'cities')
    mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-raw', Key = f'cities{current_date}')
    assert data == [{'Australia': 'Perth'}]

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