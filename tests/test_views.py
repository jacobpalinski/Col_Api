import pytest
import time
from flask import json
from httpstatus import HttpStatus
from models import (orm,User,UserSchema,BlacklistToken,Currency,CurrencySchema,Location,LocationSchema,
Home_Purchase,Home_PurchaseSchema,Rent,RentSchema,Utilities,UtilitiesSchema,
Transportation,TransportationSchema,Food_and_Beverage, Food_and_BeverageSchema,
Childcare,ChildcareSchema,Apparel, ApparelSchema, Leisure,LeisureSchema)

TEST_EMAIL = 'test@gmail.com'

def test_user_post_no_user(client):
    response = client.post('/auth/user',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'successfully registered'
    assert response.status_code == HttpStatus.created_201.value
    assert User.query.count() == 1

def test_user_post_exist_user(client):
    post_response = client.post('/auth/user',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email': TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))
    second_post_response = client.post('/auth/user',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email': TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))
    second_post_response_data = json.loads(second_post_response.get_data(as_text = True))
    assert second_post_response_data['message'] == 'User already exists. Please log in'
    assert second_post_response.status_code == HttpStatus.conflict_409.value
    assert User.query.count() == 1

@pytest.fixture
def create_user(client):
    new_user = client.post('/auth/user',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))

def test_login_valid_user(client,create_user):
    response = client.post('/auth/login',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'successfully logged in'
    assert bool(response_data.get('auth_token')) == True
    assert response.status_code == HttpStatus.ok_200.value

def test_login_invalid_user(client):
    response = client.post('/auth/login',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'User does not exist.'
    assert response.status_code == HttpStatus.notfound_404.value

@pytest.fixture
def login(client, create_user):
    login = client.post('/auth/login',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))
    login_data = json.loads(login.get_data(as_text = True))
    return login_data

def test_user_get_valid_token(client,create_user,login):
    get_response = client.get('/auth/user',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['data']['user_id'] == 1
    assert get_response_data['data']['email'] == TEST_EMAIL
    assert get_response_data['data'] == User.query(User.creation_date).filter(User.id == 1)
    assert get_response.status_code == HttpStatus.ok_200.value

def test_user_get_no_token(client):
    get_response = client.get('/auth/user',
        headers = {"Content-Type": "application/json"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['message'] == 'Provide a valid auth token'
    assert get_response.status_code == HttpStatus.forbidden_403.value

def test_user_get_invalid_token(client):
    get_response = client.get('/auth/user', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer invalid token"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['message'] == 'Invalid token. Please log in again.'
    assert get_response.status_code == HttpStatus.unauthorized_401.value

def test_user_get_expired_token(client,create_user,login):
    time.sleep(6)
    get_response = client.get('/auth/user',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['message'] == 'Signature expired. Please log in again.'
    assert get_response.status_code == HttpStatus.unauthorized_401.value
    

def test_user_get_malformed_bearer_token(client,create_user,login):
    get_response = client.get('/auth/user',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer{login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['message'] == 'Bearer token malformed'
    assert get_response.status_code == HttpStatus.unauthorized_401.value

def test_logout_valid_token(client,create_user,login):
    response = client.post('/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'successfully logged out'
    assert response.status_code == HttpStatus.ok_200.value
    assert BlacklistToken.query.count() == 1

def test_logout_no_token(client):
    response = client.post('/auth/logout',
        headers = {"Content-Type": "application/json"})
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Provide a valid auth token'
    assert response.status_code == HttpStatus.forbidden_403.value
    assert BlacklistToken.query.count() == 0

def test_logout_invalid_token(client):
    response = client.post('/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer invalid token"})
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Invalid token. Please log in again.'
    assert response.status_code == HttpStatus.bad_request_400.value
    assert BlacklistToken.query.count() == 0

def test_logout_expired_token(client,create_user,login):
    time.sleep(6)
    response = client.post('/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Signature expired. Please log in again.'
    assert response.status_code == HttpStatus.unauthorized_401.value

def test_logout_blacklisted_token(client,create_user,login):
    blacklist_token = BlacklistToken(token = login['auth_token'])
    blacklist_token.add(blacklist_token)
    assert BlacklistToken.query.count() == 1
    response = client.post('/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Token blacklisted. Please log in again'
    assert response.status_code == HttpStatus.unauthorized_401.value
    assert BlacklistToken.query.count() == 1

def test_logout_malformed_token(client,create_user,login):
    response = client.post('/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer{login['token']}"})
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Bearer token malformed'
    assert response.status_code == HttpStatus.unauthorized_401.value
    assert BlacklistToken.query.count() == 0

def test_reset_password_exist_user(client,new_user):
    response = client.post('/user/password_reset',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Password reset successful'
    assert response.status_code == HttpStatus.ok_200.value

def test_reset_password_no_user(client):
    response = client.post('/user/password_reset',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': 'X4nmasXII!'
        }))
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'User does not exist'
    assert response.status_code == HttpStatus.unauthorized_401.value

def create_currency(client, abbreviation, usd_to_local_exchange_rate):
    response = client.post('/currencies/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'abbreviation': abbreviation,
        'usd_to_local_exchange_rate': usd_to_local_exchange_rate
        }))
    return response

def test_currency_post_new_currency(client):
    response = create_currency(client,'AUD',1.45)
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['abbreviation'] == 'AUD'
    assert response_data['usd_to_local_exchange_rate'] == 1.45
    assert response.status_code == HttpStatus.created_201.value
    assert Currency.query.count() == 1

def test_currency_post_duplicated_currency(client):
    response = create_currency(client,'AUD',1.45)
    response = create_currency(client,'AUD',1.45)
    assert response.status_code == HttpStatus.bad_request_400.value
    assert Currency.query.count() == 1

def test_currency_get_with_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    get_response = client.get('/currencies/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['abbreviation'] == 'AUD'
    assert get_response_data['usd_to_local_exchange_rate'] == 1.45
    assert get_response.status_code == HttpStatus.ok_200.value

def test_currency_get_notexist_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    get_response = client.get('/currencies/2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    assert get_response.status_code == HttpStatus.notfound_404.value

def test_currency_get_without_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    get_first_page_response = client.get('/currencies/',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 2
    assert get_first_page_response_data['results'][0]['abbreviation'] == 'AUD'
    assert get_first_page_response_data['results'][0]['usd_to_local_exchange_rate'] == 1.45
    assert get_first_page_response_data['results'][1]['abbreviation'] == 'CHF'
    assert get_first_page_response_data['results'][1]['usd_to_local_exchange_rate'] == 0.92
    assert get_first_page_response_data['count'] == 2
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/currencies/?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/currencies/?page=1'
    assert get_second_page_response_data['next'] == None

def test_currency_update(client):
    create_currency(client,'AUD',1.45)
    patch_response = client.patch('/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'abbreviation': 'Aud',
        'usd_to_local_exchange_rate' : 1.50
        }))
    assert patch_response.status_code == HttpStatus.ok_200.value
    get_response = client.get('/currencies/1',
        headers = {'Content-Type': 'application/json'})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['abbreviation'] == 'Aud'
    assert get_response_data['usd_to_local_exchange_rate'] == 1.50
    assert get_response.status_code == HttpStatus.ok_200.value

def test_currency_update_no_id_exist(client):
    patch_response = client.patch('/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'abbreviation': 'Aud',
        'usd_to_local_exchange_rate' : 1.50
        }))
    assert patch_response.status_code == HttpStatus.notfound_404.value
    assert Currency.query.count() == 0

def test_currency_delete(client):
    create_currency(client,'AUD',1.45)
    delete_response = client.delete('/currencies/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.no_content_204.value
    assert Currency.query.count() == 0

def test_currency_delete_no_id_exist(client):
    delete_response = client.delete('/currencies/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.notfound_404.value
    assert Currency.query.count() == 0

def create_location(client, country, city, abbreviation):
    response = client.post('/locations/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'country': country,
        'city': city,
        'abbreviation': abbreviation
        }))
    return response

def test_location_post_new_location_currency_exist(client):
    create_currency(client,'AUD',1.45)
    post_response = create_location('Australia','Perth','AUD')
    post_response_data = json.loads(post_response.get_data(as_text = True))
    assert post_response_data['country'] == 'Australia'
    assert post_response_data['city'] == 'Perth'
    assert post_response_data['currency']['id'] == 1
    assert post_response_data['currency']['abbreviation'] == 'AUD'
    assert post_response.status_code == HttpStatus.created_201.value
    assert Location.query.count() == 1

def test_location_post_new_location_currency_none(client):
    response = create_location('Australia','Perth','AUD')
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Specified currency doesnt exist in /currencies/ API endpoint'
    assert response.status_code == HttpStatus.notfound_404.value
    assert Location.query.count() == 0

def test_location_get_with_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    get_response = client.get('/locations/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['country'] == 'Australia'
    assert get_response_data['city'] == 'Perth'
    assert get_response_data['currency']['id'] == 1
    assert get_response_data['currency']['abbreviation'] == 'AUD'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_location_get_notexist_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    get_response = client.get('/locations/2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    assert get_response.status_code == HttpStatus.notfound_404.value

def test_location_get_without_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    get_first_page_response = client.get('/locations/',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 2
    assert get_first_page_response_data['results'][0]['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['city'] == 'Perth'
    assert get_first_page_response_data['results'][0]['currency']['id'] == 1
    assert get_first_page_response_data['results'][0]['currency']['abbreviation'] == 'AUD'
    assert get_first_page_response_data['results'][1]['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][1]['currency']['id'] == 1
    assert get_first_page_response_data['results'][1]['currency']['abbreviation'] == 'AUD'
    assert get_first_page_response_data['count'] == 2
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/locations/?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/locations/?page=1'
    assert get_second_page_response_data['next'] == None

def test_location_delete(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    delete_response = client.delete('/locations/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.no_content_204.value
    assert Location.query.count() == 0

def test_location_delete_no_id_exist(client):
    delete_response = client.delete('/locations/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.notfound_404.value
    assert Location.query.count() == 0

def create_home_purchase(client,property_location,price_per_sqm,mortgage_interest,city):
    response = client.post('/homepurchase/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': property_location,
        'price_per_sqm': price_per_sqm,
        'mortgage_interest': mortgage_interest,
        'city': city
        }))
    return response

def test_home_purchase_post_home_purchase_location_exist(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    post_response = create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    post_response_data = json.loads(post_response.get_data(as_text = True))
    assert post_response_data['property_location'] == 'City Centre'
    assert post_response_data['price_per_sqm'] == 6339.73
    assert post_response_data['mortgage_interest'] == 5.09
    assert post_response_data['location']['id'] == 1
    assert post_response_data['location']['country'] == 'Australia'
    assert post_response_data['location']['city'] == 'Perth'
    assert post_response.status_code == HttpStatus.created_201.value
    assert Home_Purchase.query.count() == 1

def test_home_purchase_post_home_purchase_location_notexist(client):
    response = create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
    assert response.status_code == HttpStatus.notfound_404.value
    assert Home_Purchase.query.count() == 0

def test_home_purchase_get_with_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    get_response = client.get('/homepurchase/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['price_per_sqm'] == 6339.73
    assert get_response_data['mortgage_interest'] == 5.09
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_home_purchase_get_notexist_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_home_purchase('City Centre', 9184.02, 5.09, 'Perth')
    get_response = client.get('/homepurchase/2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    assert get_response.status_code == HttpStatus.notfound_404.value

def test_home_purchase_get_country_city_abbreviation(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252.76, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619.88, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775.24, 1.92, 'Zurich')
    get_response = client.get('/homepurchase/Australia/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response = json.loads(get_response.get_data(as_text = True))
    assert get_response['property_location'] == 'City Centre'
    assert get_response['price_per_sqm'] == 6339.73
    assert get_response['mortgage_interest'] == 5.09
    assert get_response['location']['id'] == 1
    assert get_response['location']['country'] == 'Australia'
    assert get_response['location']['city'] == 'Perth'

def test_home_purchase_get_country_city_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252.76, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619.88, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775.24, 1.92, 'Zurich')
    get_response = client.get('/homepurchase/Australia/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response = json.loads(get_response.get_data(as_text = True))
    assert get_response['property_location'] == 'City Centre'
    assert get_response['price_per_sqm'] == 6339.73
    assert get_response['mortgage_interest'] == 5.09
    assert get_response['location']['id'] == 1
    assert get_response['location']['country'] == 'Australia'
    assert get_response['location']['city'] == 'Perth'

def test_home_purchase_get_country_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252.76, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619.88, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775.24, 1.92, 'Zurich')
    get_first_page_response = client.get('/homepurchase/Australia',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['price_per_sqm'] == 6339.73
    assert get_first_page_response_data['results'][0]['mortgage_interest'] == 5.09
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['price_per_sqm'] == 7252.76
    assert get_first_page_response_data['results'][1]['mortgage_interest'] == 4.26
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['price_per_sqm'] == 14619.88
    assert get_first_page_response_data['results'][2]['mortgage_interest'] == 4.25
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/homepurchase/Australia?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/homepurchase/Australia?page=1'
    assert get_second_page_response_data['next'] == None

def test_home_purchase_get_country_none_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252.76, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619.88, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775.24, 1.92, 'Zurich')
    get_first_page_response = client.get('/homepurchase/',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 4
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['price_per_sqm'] == 6339.73
    assert get_first_page_response_data['results'][0]['mortgage_interest'] == 5.09
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['price_per_sqm'] == 7252.76
    assert get_first_page_response_data['results'][1]['mortgage_interest'] == 4.26
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['price_per_sqm'] == 14619.88
    assert get_first_page_response_data['results'][2]['mortgage_interest'] == 4.25
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['results'][3]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][3]['price_per_sqm'] == 20775.24
    assert get_first_page_response_data['results'][3]['mortgage_interest'] == 1.92
    assert get_first_page_response_data['results'][3]['location']['id'] == 4
    assert get_first_page_response_data['results'][3]['location']['country'] == 'Switzerland'
    assert get_first_page_response_data['results'][3]['location']['city'] == 'Zurich'
    assert get_first_page_response_data['count'] == 4
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/homepurchase/?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/homepurchase/?page=1'
    assert get_second_page_response_data['next'] == None

def test_home_purchase_get_city_country_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252.76, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619.88, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775.24, 1.92, 'Zurich')
    get_response = client.get('/homepurchase/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response = json.loads(get_response.get_data(as_text = True))
    assert get_response['property_location'] == 'City Centre'
    assert get_response['price_per_sqm'] == 6339.73
    assert get_response['mortgage_interest'] == 5.09
    assert get_response['location']['id'] == 1
    assert get_response['location']['country'] == 'Australia'
    assert get_response['location']['city'] == 'Perth'

def test_home_purchase_get_abbreviation_country_none_city_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252.76, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619.88, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775.24, 1.92, 'Zurich')
    get_first_page_response = client.get('/homepurchase/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['price_per_sqm'] == 6339.73
    assert get_first_page_response_data['results'][0]['mortgage_interest'] == 5.09
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['price_per_sqm'] == 7252.76
    assert get_first_page_response_data['results'][1]['mortgage_interest'] == 4.26
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['price_per_sqm'] == 14619.88
    assert get_first_page_response_data['results'][2]['mortgage_interest'] == 4.25
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/homepurchase/AUD?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/homepurchase/AUD?page=1'
    assert get_second_page_response_data['next'] == None

def test_home_purchase_update(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    patch_response = client.patch('/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'price_per_sqm': 7000,
        'mortgage_interest': 6.01
        }))
    assert patch_response.status_code == HttpStatus.ok_200.value
    get_response = client.get('/homepurchase/1',
        headers = {'Content-Type': 'application/json'})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'Outside City Centre'
    assert get_response_data['price_per_sqm'] == 7000
    assert get_response_data['mortgage_interest'] == 6.01
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_home_purchase_update_no_id_exist(client):
    patch_response = client.patch('/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'price_per_sqm': 7000,
        'mortgage_interest': 6.01
        }))
    assert patch_response.status_code == HttpStatus.notfound_404.value
    assert Home_Purchase.query.count() == 0

def test_home_purchase_delete(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_home_purchase('City Centre', 6339.73, 5.09, 'Perth')
    delete_response = client.delete('/homepurchase/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.no_content_204.value
    assert Home_Purchase.query.count() == 0

def test_home_purchase_delete_no_id_exist(client):
    delete_response = client.delete('/locations/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.notfound_404.value
    assert Home_Purchase.query.count() == 0

def create_rent(client,property_location,bedrooms,monthly_price,city):
    response = client.post('/locations/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': property_location,
        'bedrooms': bedrooms,
        'monthly_price': monthly_price,
        'city': city
        }))
    return response

def test_rent_post_new_rent_location_exist(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    post_response = create_rent('City Centre', 1, 1642.43 , 'Perth')
    post_response_data = json.loads(post_response.get_data(as_text = True))
    assert post_response_data['property_location'] == 'City Centre'
    assert post_response_data['bedrooms'] == 1
    assert post_response_data['monthly_price'] == 1642.43
    assert post_response_data['location']['id'] == 1
    assert post_response_data['location']['country'] == 'Australia'
    assert post_response_data['location']['city'] == 'Perth'
    assert post_response.status_code == HttpStatus.created_201.value
    assert Rent.query.count() == 1

def test_rent_post_location_notexist(client):
    response = create_rent('City Centre', 1, 1642.43, 'Perth')
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
    assert response.status_code == HttpStatus.notfound_404.value
    assert Rent.query.count() == 0

def test_rent_get_with_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    get_response = client.get('/rent/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 1642.43
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_rent_get_notexist_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    get_response = client.get('/rent/2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    assert get_response.status_code == HttpStatus.notfound_404.value

def test_rent_get_country_city_abbreviation(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    create_rent('City Centre', 1, 1408.25, 'Melbourne')
    create_rent('City Centre', 1, 1999.98, 'Sydney')
    create_rent('City Centre', 1, 2263.05, 'Zurich')
    get_response = client.get('/rent/Australia/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 1642.43
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_rent_get_country_city_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    create_rent('City Centre', 1, 1408.25, 'Melbourne')
    create_rent('City Centre', 1, 1999.98, 'Sydney')
    create_rent('City Centre', 1, 2263.05, 'Zurich')
    get_response = client.get('/rent/Australia/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 1642.43
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_rent_get_country_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    create_rent('City Centre', 1, 1408.25, 'Melbourne')
    create_rent('City Centre', 1, 1999.98, 'Sydney')
    create_rent('City Centre', 1, 2263.05, 'Zurich')
    get_first_page_response = client.get('/rent/Australia',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['bedrooms'] == 1
    assert get_first_page_response_data['results'][0]['monthly_price'] == 1642.43
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['bedrooms'] == 1
    assert get_first_page_response_data['results'][1]['monthly_price'] == 1408.25
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['bedrooms'] == 1
    assert get_first_page_response_data['results'][2]['monthly_price'] == 1999.98
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/rent/Australia?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/rent/Australia?page=1'
    assert get_second_page_response_data['next'] == None

def test_rent_get_country_none_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    create_rent('City Centre', 1, 1408.25, 'Melbourne')
    create_rent('City Centre', 1, 1999.98, 'Sydney')
    create_rent('City Centre', 1, 2263.05, 'Zurich')
    get_first_page_response = client.get('/rent/',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 4
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['bedrooms'] == 1
    assert get_first_page_response_data['results'][0]['monthly_price'] == 1642.43
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['bedrooms'] == 1
    assert get_first_page_response_data['results'][1]['monthly_price'] == 1408.25
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['bedrooms'] == 1
    assert get_first_page_response_data['results'][2]['monthly_price'] == 1999.98
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['results'][3]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][3]['bedrooms'] == 1
    assert get_first_page_response_data['results'][3]['monthly_price'] == 2263.05
    assert get_first_page_response_data['results'][3]['location']['id'] == 4
    assert get_first_page_response_data['results'][3]['location']['country'] == 'Switzerland'
    assert get_first_page_response_data['results'][3]['location']['city'] == 'Zurich'
    assert get_first_page_response_data['count'] == 4
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/rent/?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/homepurchase/?page=1'
    assert get_second_page_response_data['next'] == None

def test_rent_get_city_country_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    create_rent('City Centre', 1, 1408.25, 'Melbourne')
    create_rent('City Centre', 1, 1999.98, 'Sydney')
    create_rent('City Centre', 1, 2263.05, 'Zurich')
    get_response = client.get('/rent/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 1642.43
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_rent_get_abbreviation_country_none_city_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    create_rent('City Centre', 1, 1408.25, 'Melbourne')
    create_rent('City Centre', 1, 1999.98, 'Sydney')
    create_rent('City Centre', 1, 2263.05, 'Zurich')
    get_first_page_response = client.get('/rent/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['bedrooms'] == 1
    assert get_first_page_response_data['results'][0]['monthly_price'] == 1642.43
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['bedrooms'] == 1
    assert get_first_page_response_data['results'][1]['monthly_price'] == 1408.25
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['bedrooms'] == 1
    assert get_first_page_response_data['results'][2]['monthly_price'] == 1999.98
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/rent/AUD?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/rent/AUD?page=1'
    assert get_second_page_response_data['next'] == None












































    
