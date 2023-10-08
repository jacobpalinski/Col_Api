import pytest
import requests_mock
import boto3
import os
import json
import datetime
from utils.spark_utils import create_spark_session

@pytest.fixture
def current_date():
    return datetime.date.today().strftime('%Y%m%d')

@pytest.fixture
def mock_currency_conversion_rates_html():
    with open('mock_html/numbeo_currency_conversion.html', encoding = 'utf-8') as html_content:
        html = html_content.read()
        yield html

@pytest.fixture
def mock_environment_variables(mocker):
    mocker.patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'access-key',
        'AWS_SECRET_ACCESS_KEY': 'secret-key',
        'S3_BUCKET_RAW': 'test-bucket-raw',
        'S3_BUCKET_TRANSFORMED': 'test-bucket-transformed'
    })

@ pytest.fixture
def mock_boto3_s3(mocker, monkeypatch):
    mock_s3 = mocker.Mock()
    monkeypatch.setattr(boto3, 'client', lambda *args, **kwargs: mock_s3)

    # Current date for return_value prefixes
    current_date = datetime.date.today().strftime('%Y%m%d')

    return_values = {
        f'cities{current_date}': {'Body': mocker.MagicMock(read=mocker.MagicMock(return_value=json.dumps([{'Australia': 'Perth'}]).encode('utf-8')))},
        # Add more mappings for different prefixes as needed
    }

    def mock_get_object(Bucket, Key, **kwargs):
        # Extract the prefix from the Key
        file_prefix = Key[:]

        # Return the corresponding value from return_values
        return return_values.get(file_prefix, {})

    mock_s3.get_object.side_effect = mock_get_object
    return mock_s3

@pytest.fixture
def mock_locations_with_cities_html():
    with open('mock_html/numbeo_country_page_with_cities.html', encoding = 'utf-8') as html_content:
        html = html_content.read()
        yield html

@pytest.fixture
def mock_locations_without_cities_html():
    with open('mock_html/numbeo_country_page_without_cities.html', encoding = 'utf-8') as html_content:
        html = html_content.read()
        yield html

@pytest.fixture
def mock_countries_with_cities():
    # Only use 1 country for testing extract_cities
    return ['Australia']

@pytest.fixture
def mock_countries_without_cities():
    # Only use 1 country for testing extract_cities
    return ['Hong Kong']

@pytest.fixture
def mock_numbeo_prices_perth_html():
    with open('mock_html/numbeo_prices_perth.html', encoding = 'utf-8') as html_content:
        html = html_content.read()
        yield html

@pytest.fixture
def mock_livingcost_prices_perth_html():
    with open('mock_html/livingcost_prices_perth.html', encoding = 'utf-8') as html_content:
        html = html_content.read()
        yield html

@pytest.fixture
def pyspark_session():
    session = create_spark_session('test_spark_session')
    yield session
    session.stop()