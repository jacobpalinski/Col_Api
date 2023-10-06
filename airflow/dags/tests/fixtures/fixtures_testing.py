import pytest
import requests_mock
import boto3
import os
import json

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
        'S3_BUCKET_RAW': 'bucket'
    })

@ pytest.fixture
def mock_boto3_s3(mocker, monkeypatch):
    mock_s3 = mocker.Mock()
    monkeypatch.setattr(boto3, 'client', lambda *args, **kwargs: mock_s3)
    mock_s3.get_object.return_value = {'Body': mocker.MagicMock(read = mocker.MagicMock(return_value = json.dumps(['Perth']).encode('utf-8')))}
    return mock_s3

@pytest.fixture
def mock_extract_cities_html():
    with open('mock_html/numbeo_country_page.html', encoding = 'utf-8') as html_content:
        html = html_content.read()
        yield html

@pytest.fixture
def mock_countries():
    # Only use 1 country for testing extract_cities
    return ['Australia']

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
def mock_spark_session(mocker):
    mock_spark_session = mocker.Mock()
    mocker.patch('pyspark.sql.SparkSession.builder.getOrCreate', return_value = mock_spark_session)