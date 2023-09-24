import pytest
import requests_mock
import boto3

@pytest.fixture
def mock_currency_conversion_rates_html():
    with open('mock_html/numbeo_currency_conversion.html', encoding = 'utf-8') as html_content:
        html = html_content.read()
        yield html

@ pytest.fixture
def mock_boto3_s3(mocker, monkeypatch):
    mock_s3 = mocker.Mock()
    monkeypatch.setattr(boto3, 'client', lambda *args, **kwargs: mock_s3)
    return mock_s3