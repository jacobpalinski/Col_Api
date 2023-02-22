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
    post_response = create_home_purchase('City Centre', 6339, 5.09, 'Perth')
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
    response = create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
    assert response.status_code == HttpStatus.notfound_404.value
    assert Home_Purchase.query.count() == 0

def test_home_purchase_get_with_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    get_response = client.get('/homepurchase/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['price_per_sqm'] == 6339
    assert get_response_data['mortgage_interest'] == 5.09
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_home_purchase_get_notexist_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
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
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775, 1.92, 'Zurich')
    get_response = client.get('/homepurchase/Australia/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response = json.loads(get_response.get_data(as_text = True))
    assert get_response['property_location'] == 'City Centre'
    assert get_response['price_per_sqm'] == 9191.55
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
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775, 1.92, 'Zurich')
    get_response = client.get('/homepurchase/Australia/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response = json.loads(get_response.get_data(as_text = True))
    assert get_response['property_location'] == 'City Centre'
    assert get_response['price_per_sqm'] == 6339
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
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775, 1.92, 'Zurich')
    get_first_page_response = client.get('/homepurchase/Australia',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['price_per_sqm'] == 6339
    assert get_first_page_response_data['results'][0]['mortgage_interest'] == 5.09
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['price_per_sqm'] == 7252
    assert get_first_page_response_data['results'][1]['mortgage_interest'] == 4.26
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['price_per_sqm'] == 14619
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

def test_home_purchase_get_country_abbreviation_city_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775, 1.92, 'Zurich')
    get_first_page_response = client.get('/homepurchase/Australia/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['price_per_sqm'] == 9191.55
    assert get_first_page_response_data['results'][0]['mortgage_interest'] == 5.09
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['price_per_sqm'] == 10515.4
    assert get_first_page_response_data['results'][1]['mortgage_interest'] == 4.26
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['price_per_sqm'] == 21197.55
    assert get_first_page_response_data['results'][2]['mortgage_interest'] == 4.25
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/homepurchase/Australia/AUD?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/homepurchase/Australia/AUD?page=1'
    assert get_second_page_response_data['next'] == None

def test_home_purchase_get_city_abbreviation_country_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775, 1.92, 'Zurich')
    get_response = client.get('/homepurchase/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response['property_location'] == 'City Centre'
    assert get_response['price_per_sqm'] == 9191.5
    assert get_response['mortgage_interest'] == 5.09
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value


def test_home_purchase_get_country_none_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775, 1.92, 'Zurich')
    get_first_page_response = client.get('/homepurchase/',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 4
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['price_per_sqm'] == 6339
    assert get_first_page_response_data['results'][0]['mortgage_interest'] == 5.09
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['price_per_sqm'] == 7252
    assert get_first_page_response_data['results'][1]['mortgage_interest'] == 4.26
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['price_per_sqm'] == 14619
    assert get_first_page_response_data['results'][2]['mortgage_interest'] == 4.25
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['results'][3]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][3]['price_per_sqm'] == 20775
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
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775, 1.92, 'Zurich')
    get_response = client.get('/homepurchase/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response = json.loads(get_response.get_data(as_text = True))
    assert get_response['property_location'] == 'City Centre'
    assert get_response['price_per_sqm'] == 6339
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
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    create_home_purchase('City Centre', 7252, 4.26, 'Melbourne')
    create_home_purchase('City Centre', 14619, 4.25, 'Sydney')
    create_home_purchase('City Centre', 20775, 1.92, 'Zurich')
    get_first_page_response = client.get('/homepurchase/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['price_per_sqm'] == 9191.55
    assert get_first_page_response_data['results'][0]['mortgage_interest'] == 5.09
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['price_per_sqm'] == 10,515.4
    assert get_first_page_response_data['results'][1]['mortgage_interest'] == 4.26
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['price_per_sqm'] == 21197.55
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
    create_home_purchase('City Centre', 6339, 5.09, 'Perth')
    delete_response = client.delete('/homepurchase/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.no_content_204.value
    assert Home_Purchase.query.count() == 0

def test_home_purchase_delete_no_id_exist(client):
    delete_response = client.delete('/homepurchase/1',
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
    post_response = create_rent('City Centre', 1, 1642 , 'Perth')
    post_response_data = json.loads(post_response.get_data(as_text = True))
    assert post_response_data['property_location'] == 'City Centre'
    assert post_response_data['bedrooms'] == 1
    assert post_response_data['monthly_price'] == 1642
    assert post_response_data['location']['id'] == 1
    assert post_response_data['location']['country'] == 'Australia'
    assert post_response_data['location']['city'] == 'Perth'
    assert post_response.status_code == HttpStatus.created_201.value
    assert Rent.query.count() == 1

def test_rent_post_location_notexist(client):
    response = create_rent('City Centre', 1, 1642, 'Perth')
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
    assert response.status_code == HttpStatus.notfound_404.value
    assert Rent.query.count() == 0

def test_rent_get_with_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_rent('City Centre', 1, 1642, 'Perth')
    get_response = client.get('/rent/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 1642
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_rent_get_notexist_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_rent('City Centre', 1, 1642, 'Perth')
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
    create_rent('City Centre', 1, 1642, 'Perth')
    create_rent('City Centre', 1, 1408, 'Melbourne')
    create_rent('City Centre', 1, 1999, 'Sydney')
    create_rent('City Centre', 1, 2263, 'Zurich')
    get_response = client.get('/rent/Australia/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 2380.9
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
    create_rent('City Centre', 1, 1642, 'Perth')
    create_rent('City Centre', 1, 1408, 'Melbourne')
    create_rent('City Centre', 1, 1999, 'Sydney')
    create_rent('City Centre', 1, 2263, 'Zurich')
    get_response = client.get('/rent/Australia/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 1642
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
    create_rent('City Centre', 1, 1642, 'Perth')
    create_rent('City Centre', 1, 1408, 'Melbourne')
    create_rent('City Centre', 1, 1999, 'Sydney')
    create_rent('City Centre', 1, 2263, 'Zurich')
    get_first_page_response = client.get('/rent/Australia',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['bedrooms'] == 1
    assert get_first_page_response_data['results'][0]['monthly_price'] == 1642
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['bedrooms'] == 1
    assert get_first_page_response_data['results'][1]['monthly_price'] == 1408
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['bedrooms'] == 1
    assert get_first_page_response_data['results'][2]['monthly_price'] == 1999
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

def test_rent_get_country_abbreviation_city_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642, 'Perth')
    create_rent('City Centre', 1, 1408, 'Melbourne')
    create_rent('City Centre', 1, 1999, 'Sydney')
    create_rent('City Centre', 1, 2263, 'Zurich')
    get_first_page_response = client.get('/rent/Australia/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['bedrooms'] == 1
    assert get_first_page_response_data['results'][0]['monthly_price'] == 2380.9
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['bedrooms'] == 1
    assert get_first_page_response_data['results'][1]['monthly_price'] == 2041.6
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['bedrooms'] == 1
    assert get_first_page_response_data['results'][2]['monthly_price'] == 2898.55
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/rent/Australia/AUD?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/rent/Australia/AUD?page=1'
    assert get_second_page_response_data['next'] == None

def test_rent_get_city_abbreviation_country_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642, 'Perth')
    create_rent('City Centre', 1, 1408, 'Melbourne')
    create_rent('City Centre', 1, 1999, 'Sydney')
    create_rent('City Centre', 1, 2263, 'Zurich')
    get_response = client.get('/rent/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 2380.9
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value


def test_rent_get_country_none_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_rent('City Centre', 1, 1642, 'Perth')
    create_rent('City Centre', 1, 1408, 'Melbourne')
    create_rent('City Centre', 1, 1999, 'Sydney')
    create_rent('City Centre', 1, 2263, 'Zurich')
    get_first_page_response = client.get('/rent/',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 4
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['bedrooms'] == 1
    assert get_first_page_response_data['results'][0]['monthly_price'] == 1642
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['bedrooms'] == 1
    assert get_first_page_response_data['results'][1]['monthly_price'] == 1408
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['bedrooms'] == 1
    assert get_first_page_response_data['results'][2]['monthly_price'] == 1999
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['results'][3]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][3]['bedrooms'] == 1
    assert get_first_page_response_data['results'][3]['monthly_price'] == 2263
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
    create_rent('City Centre', 1, 1642, 'Perth')
    create_rent('City Centre', 1, 1408, 'Melbourne')
    create_rent('City Centre', 1, 1999, 'Sydney')
    create_rent('City Centre', 1, 2263, 'Zurich')
    get_response = client.get('/rent/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'City Centre'
    assert get_response_data['bedrooms'] == 1
    assert get_response_data['monthly_price'] == 1642
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
    create_rent('City Centre', 1, 1642, 'Perth')
    create_rent('City Centre', 1, 1408, 'Melbourne')
    create_rent('City Centre', 1, 1999, 'Sydney')
    create_rent('City Centre', 1, 2263, 'Zurich')
    get_first_page_response = client.get('/rent/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][0]['bedrooms'] == 1
    assert get_first_page_response_data['results'][0]['monthly_price'] == 2380.9
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][1]['bedrooms'] == 1
    assert get_first_page_response_data['results'][1]['monthly_price'] == 2041.6
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['property_location'] == 'City Centre'
    assert get_first_page_response_data['results'][2]['bedrooms'] == 1
    assert get_first_page_response_data['results'][2]['monthly_price'] == 2898.55
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

def test_rent_update(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_rent('City Centre', 1, 1642, 'Perth')
    patch_response = client.patch('/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'bedrooms': 3,
        'monthly_price': 2526
        }))
    assert patch_response.status_code == HttpStatus.ok_200.value
    get_response = client.get('/rent/1',
        headers = {'Content-Type': 'application/json'})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['property_location'] == 'Outside City Centre'
    assert get_response_data['bedrooms'] == 3
    assert get_response_data['monthly_price'] == 2526
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_rent_update_no_id_exist(client):
    patch_response = client.patch('/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'bedrooms': 3,
        'monthly_price': 2526.62
        }))
    assert patch_response.status_code == HttpStatus.notfound_404.value
    assert Rent.query.count() == 0

def test_rent_delete(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_rent('City Centre', 1, 1642.43, 'Perth')
    delete_response = client.delete('/rent/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.no_content_204.value
    assert Rent.query.count() == 0

def test_rent_delete_no_id_exist(client):
    delete_response = client.delete('/rent/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.notfound_404.value
    assert Rent.query.count() == 0

def create_utilities(client,utility,monthly_price,city):
    response = client.post('/utilities/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'utility': utility,
        'monthly_price': monthly_price,
        'city': city
        }))
    return response

def test_utilities_post_utilities_location_exist(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    post_response = create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    post_response_data = json.loads(post_response.get_data(as_text = True))
    assert post_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert post_response_data['monthly_price'] == 210
    assert post_response_data['location']['id'] == 1
    assert post_response_data['location']['country'] == 'Australia'
    assert post_response_data['location']['city'] == 'Perth'
    assert post_response.status_code == HttpStatus.created_201.value
    assert Utilities.query.count() == 1

def test_utilties_post_utilities_location_notexist(client):
    response = create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
    assert response.status_code == HttpStatus.notfound_404.value
    assert Utilities.query.count() == 0

def test_utilities_get_with_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    get_response = client.get('/utilities/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_response_data['monthly_price'] == 210
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_utilities_get_notexist_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    get_response = client.get('/utilities/2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    assert get_response.status_code == HttpStatus.notfound_404.value

def test_utilities_get_country_city_abbreviation(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
    get_response = client.get('/utilities/Australia/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_response_data['monthly_price'] == 304.5
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_utilities_get_country_city_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
    get_response = client.get('/utilities/Australia/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_response_data['monthly_price'] == 210
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_utilities_get_country_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
    get_first_page_response = client.get('/utilities/Australia',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][0]['monthly_price'] == 210
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][1]['monthly_price'] == 172
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][2]['monthly_price'] == 174
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/utilities/Australia?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/utilities/Australia?page=1'
    assert get_second_page_response_data['next'] == None

def test_utilities_get_country_abbreviation_city_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
    get_first_page_response = client.get('/utilities/Australia/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][0]['monthly_price'] == 304.5
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][1]['monthly_price'] == 249.4
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][2]['monthly_price'] == 252.3
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/utilities/Australia/AUD?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/utilities/Australia/AUD?page=1'
    assert get_second_page_response_data['next'] == None

def test_utilities_get_city_abbreviation_country_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
    get_response = client.get('/utilities/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_response_data['monthly_price'] == 304.5
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value


def test_utilities_get_country_none_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
    get_first_page_response = client.get('/utilities/',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 4
    assert get_first_page_response_data['results'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][0]['monthly_price'] == 210
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][1]['monthly_price'] == 172
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][2]['monthly_price'] == 174
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['results'][3]['utility'] == 'City Centre'
    assert get_first_page_response_data['results'][3]['monthly_price'] == 273
    assert get_first_page_response_data['results'][3]['location']['id'] == 4
    assert get_first_page_response_data['results'][3]['location']['country'] == 'Switzerland'
    assert get_first_page_response_data['results'][3]['location']['city'] == 'Zurich'
    assert get_first_page_response_data['count'] == 4
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/utilities/?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/utilities/?page=1'
    assert get_second_page_response_data['next'] == None

def test_utilities_get_city_country_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
    get_response = client.get('/utilities/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_response_data['monthly_price'] == 210
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_utilities_get_abbreviation_country_none_city_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
    get_first_page_response = client.get('/utilities/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][0]['monthly_price'] == 304.5
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][1]['monthly_price'] == 249.5
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_first_page_response_data['results'][2]['monthly_price'] == 252.3
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/utilities/AUD?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/utilities/AUD?page=1'
    assert get_second_page_response_data['next'] == None

def test_utilities_update(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    patch_response = client.patch('/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'utility': 'Internet',
        'monthly_price': 55
        }))
    assert patch_response.status_code == HttpStatus.ok_200.value
    get_response = client.get('/utilities/1',
        headers = {'Content-Type': 'application/json'})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
    assert get_response_data['monthly_price'] == 55
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_utilities_update_no_id_exist(client):
    patch_response = client.patch('/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'utility': 'Internet',
        'monthly_price': 55
        }))
    assert patch_response.status_code == HttpStatus.notfound_404.value
    assert Utilities.query.count() == 0

def test_utilities_delete(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_utilities('Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
    delete_response = client.delete('/utilities/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.no_content_204.value
    assert Utilities.query.count() == 0

def test_utilities_delete_no_id_exist(client):
    delete_response = client.delete('/utilities/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.notfound_404.value
    assert Utilities.query.count() == 0

def create_transportation(client,type,price,city):
    response = client.post('/utilities/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': type,
        'price': price,
        'city': city
        }))
    return response

def test_transportation_post_transportation_location_exist(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    post_response = create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    post_response_data = json.loads(post_response.get_data(as_text = True))
    assert post_response_data['type'] == 'Monthly Public Transportation Pass'
    assert post_response_data['price'] == 103
    assert post_response_data['location']['id'] == 1
    assert post_response_data['location']['country'] == 'Australia'
    assert post_response_data['location']['city'] == 'Perth'
    assert post_response.status_code == HttpStatus.created_201.value
    assert Transportation.query.count() == 1

def test_transportation_post_transportation_location_notexist(client):
    response = create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    response_data = json.loads(response.get_data(as_text = True))
    assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
    assert response.status_code == HttpStatus.notfound_404.value
    assert Transportation.query.count() == 0

def test_transportation_get_with_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    get_response = client.get('/transportation/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['type'] == 'Monthly Public Transportation Pass'
    assert get_response_data['price'] == 103
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_transportation_get_notexist_id(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    get_response = client.get('/transportation/2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    assert get_response.status_code == HttpStatus.notfound_404.value

def test_transportation_get_country_city_abbreviation(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    create_transportation('Monthly Public Transportation Pass', 112, 'Melbourne')
    create_transportation('Monthly Public Transportation Pass', 150, 'Sydney')
    create_transportation('Monthly Public Transportation Pass', 102, 'Zurich')
    get_response = client.get('/transportation/Australia/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['type'] == 'Monthly Public Transportation Pass'
    assert get_response_data['price'] == 149.35
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_transportation_get_country_city_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    create_transportation('Monthly Public Transportation Pass', 112, 'Melbourne')
    create_transportation('Monthly Public Transportation Pass', 150, 'Sydney')
    create_transportation('Monthly Public Transportation Pass', 102, 'Zurich')
    get_response = client.get('/transportation/Australia/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['type'] == 'Monthly Public Transportation Pass'
    assert get_response_data['price'] == 103
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_transportation_get_country_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    create_transportation('Monthly Public Transportation Pass', 112, 'Melbourne')
    create_transportation('Monthly Public Transportation Pass', 150, 'Sydney')
    create_transportation('Monthly Public Transportation Pass', 102, 'Zurich')
    get_first_page_response = client.get('/transportation/Australia',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][0]['price'] == 103
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][1]['price'] == 112
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][2]['price'] == 150
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/transportation/Australia?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/transportation/Australia?page=1'
    assert get_second_page_response_data['next'] == None

def test_transportation_get_country_abbreviation_city_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    create_transportation('Monthly Public Transportation Pass', 112, 'Melbourne')
    create_transportation('Monthly Public Transportation Pass', 150, 'Sydney')
    create_transportation('Monthly Public Transportation Pass', 102, 'Zurich')
    get_first_page_response = client.get('/transportation/Australia/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][0]['price'] == 149.61
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][1]['price'] == 163.70
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][2]['price'] == 217.65
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/transportation/Australia/AUD?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/transportation/Australia/AUD?page=1'
    assert get_second_page_response_data['next'] == None

def test_transportation_get_city_abbreviation_country_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    create_transportation('Monthly Public Transportation Pass', 112, 'Melbourne')
    create_transportation('Monthly Public Transportation Pass', 150, 'Sydney')
    create_transportation('Monthly Public Transportation Pass', 102, 'Zurich')
    get_response = client.get('/transportation/Perth/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['type'] == 'Monthly Public Transportation Pass'
    assert get_response_data['price'] == 149.61
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_transportation_get_country_none_city_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    create_transportation('Monthly Public Transportation Pass', 112, 'Melbourne')
    create_transportation('Monthly Public Transportation Pass', 150, 'Sydney')
    create_transportation('Monthly Public Transportation Pass', 102, 'Zurich')
    get_first_page_response = client.get('/transportation/Australia/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 4
    assert get_first_page_response_data['results'][0]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][0]['price'] == 103
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][1]['price'] == 112
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][2]['price'] == 150
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['results'][3]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][3]['price'] == 102
    assert get_first_page_response_data['results'][3]['location']['id'] == 4
    assert get_first_page_response_data['results'][3]['location']['country'] == 'Switzerland'
    assert get_first_page_response_data['results'][3]['location']['city'] == 'Zurich'
    assert get_first_page_response_data['count'] == 4
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/transportation/?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/transportation/?page=1'
    assert get_second_page_response_data['next'] == None

def test_transportation_get_city_country_none_abbreviation_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    create_transportation('Monthly Public Transportation Pass', 112, 'Melbourne')
    create_transportation('Monthly Public Transportation Pass', 150, 'Sydney')
    create_transportation('Monthly Public Transportation Pass', 102, 'Zurich')
    get_response = client.get('/transportation/Perth',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['type'] == 'Monthly Public Transportation Pass'
    assert get_response_data['price'] == 103
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_transportation_get_abbreviation_country_none_city_none(client,create_user,login):
    create_currency(client,'AUD',1.45)
    create_currency(client,'CHF',0.92)
    create_location('Australia','Perth','AUD')
    create_location('Australia','Melbourne','AUD')
    create_location('Australia','Sydney','AUD')
    create_location('Switzerland','Zurich','CHF')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    create_transportation('Monthly Public Transportation Pass', 112, 'Melbourne')
    create_transportation('Monthly Public Transportation Pass', 150, 'Sydney')
    create_transportation('Monthly Public Transportation Pass', 102, 'Zurich')
    get_first_page_response = client.get('/transportation/AUD',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
    assert len(get_first_page_response_data['results']) == 3
    assert get_first_page_response_data['results'][0]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][0]['price'] == 149
    assert get_first_page_response_data['results'][0]['location']['id'] == 1
    assert get_first_page_response_data['results'][0]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][0]['location']['city'] == 'Perth'
    assert get_first_page_response_data['results'][1]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][1]['price'] == 163
    assert get_first_page_response_data['results'][1]['location']['id'] == 2
    assert get_first_page_response_data['results'][1]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][1]['location']['city'] == 'Melbourne'
    assert get_first_page_response_data['results'][2]['type'] == 'Monthly Public Transportation Pass'
    assert get_first_page_response_data['results'][2]['price'] == 217
    assert get_first_page_response_data['results'][2]['location']['id'] == 3
    assert get_first_page_response_data['results'][2]['location']['country'] == 'Australia'
    assert get_first_page_response_data['results'][2]['location']['city'] == 'Sydney'
    assert get_first_page_response_data['count'] == 3
    assert get_first_page_response_data['previous'] == None
    assert get_first_page_response_data['next'] == None
    get_second_page_response = client.get('/transportation/AUD?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['token']}"})
    get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
    assert len(get_second_page_response['results']) == 0
    assert get_second_page_response_data['previous'] != None
    assert get_second_page_response_data['previous'] == '/transportation/AUD?page=1'
    assert get_second_page_response_data['next'] == None

def test_transportation_update(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    patch_response = client.patch('/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': 'One-Way Ticket',
        'price': 2.76
        }))
    assert patch_response.status_code == HttpStatus.ok_200.value
    get_response = client.get('/transportation/1',
        headers = {'Content-Type': 'application/json'})
    get_response_data = json.loads(get_response.get_data(as_text = True))
    assert get_response_data['type'] == 'One-Way Ticket'
    assert get_response_data['price'] == 2.76
    assert get_response_data['location']['id'] == 1
    assert get_response_data['location']['country'] == 'Australia'
    assert get_response_data['location']['city'] == 'Perth'
    assert get_response.status_code == HttpStatus.ok_200.value

def test_transportation_update_no_id_exist(client):
    patch_response = client.patch('/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': 'One-Way Ticket',
        'price': 2.76
        }))
    assert patch_response.status_code == HttpStatus.notfound_404.value
    assert Transportation.query.count() == 0

def test_transportation_delete(client):
    create_currency(client,'AUD',1.45)
    create_location('Australia','Perth','AUD')
    create_transportation('Monthly Public Transportation Pass', 103, 'Perth')
    delete_response = client.delete('/transportation/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.no_content_204.value
    assert Transportation.query.count() == 0

def test_transportation_delete_no_id_exist(client):
    delete_response = client.delete('/transportation/1',
        headers = {'Content-Type': 'application/json'})
    assert delete_response.status_code == HttpStatus.notfound_404.value
    assert Transportation.query.count() == 0

















































    