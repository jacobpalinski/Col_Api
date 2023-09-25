import requests
from bs4 import BeautifulSoup

# Countries to extract cities from
countries = ['United Arab Emirates', 'Albania', 'Armenia', 'Australia', 'Azerbaijan', 'Bosnia and Herzegovina', 'Bahrain', 'Bulgaria',
    'Belarus', 'Brazil', 'Canada', 'Switzerland', 'Liechtenstein', 'Chile', 'China', 'Colombia', 'Czech Republic', 'Denmark', 'Faroe Islands', 'Andorra',
    'Austria', 'Belgium', 'Croatia', 'Cyprus', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Ireland', 'Italy', 'Kosovo', 'Latvia',
    'Lithuania', 'Luxembourg', 'Malta', 'Montenegro', 'Monaco', 'Netherlands', 'Portugal', 'San Marino', 'Slovakia', 'Slovenia', 'Spain',
    'Georgia', 'Hong Kong (China)', 'Hungary', 'Israel', 'Japan', 'South Korea', 'Macau', 'Malaysia', 'Mexico', 'Moldova', 'New Zealand',
    'North Macedonia' 'Norway', 'Oman', 'Poland', 'Qatar', 'Romania', 'Russia', 'Saudi Arabia', 'Serbia', 'Singapore', 'Sweden', 'Taiwan',
    'Thailand', 'Turkey', 'Ukraine', 'United Kingdom', 'Gibraltar', 'Isle of Man', 'Jersey', 'Uruguay', 'United States', 'Ecuador', 'Paraguay', 'Argentina']

def extract_cities(countries):
    # Cities
    cities = []

    for country in countries:
        # Request
        response = requests.get(f'https://www.numbeo.com/cost-of-living/country_result.jsp?country={country}')
        
        # Parse Html
        numbeo_country_html = BeautifulSoup(response.text, 'html.parser')
        rows = numbeo_country_html.find('table', {'id': 't2'}).find('tbody').find_all('tr')
        for row in rows:
            city = row.find('a').text
            cities.append(city)
    
    return cities
