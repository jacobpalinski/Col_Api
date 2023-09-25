import pytest
import requests
import requests_mock
from scripts.extract_cities import *
from tests.fixtures.extract_cities_html import mock_extract_cities_html

def test_extract_cities(monkeypatch, requests_mock, mock_extract_cities_html):
    # Only use 1 country for testing purposes
    mock_countries = ['Australia']
    requests_mock.get('https://www.numbeo.com/cost-of-living/country_result.jsp?country=Australia', text = mock_extract_cities_html)
    cities = extract_cities(mock_countries)
    assert cities == ['Canberra', 'Adelaide', 'Perth', 'Brisbane', 'Sydney', 'Melbourne', 'Newcastle', 'Gold Coast', 'Hobart']