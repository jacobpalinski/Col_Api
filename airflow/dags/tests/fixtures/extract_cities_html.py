import pytest

@pytest.fixture
def mock_extract_cities_html():
    with open('mock_html/numbeo_country_page.html', encoding = 'utf-8') as html_content:
        html = html_content.read()
        yield html
    