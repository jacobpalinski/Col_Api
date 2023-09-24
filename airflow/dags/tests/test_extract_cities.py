import pytest
import requests
import requests_mock
from scripts.extract_cities import extract_cities

def test_extract_cities(requests_mock, mock_extract_cities_html):
    requests_mock.get('https://www.numbeo.com/cost-of-living/country_result.jsp?country=Australia', text = mock_extract_cities_html)
    cities = extract_cities()
    assert cities == ['Canberra', 'Adelaide', 'Perth', 'Brisbane', 'Sydney', 'Melbourne', 'Newcastle', 'Gold Coast', 'Hobart']