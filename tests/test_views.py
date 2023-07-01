import pytest
import time
import os
from flask import json
from httpstatus import HttpStatus
from models import (orm,User,UserSchema,BlacklistToken,Currency,CurrencySchema,Location,LocationSchema,
HomePurchase,HomePurchaseSchema,Rent,RentSchema,Utilities,UtilitiesSchema,
Transportation,TransportationSchema,FoodBeverage, FoodBeverageSchema,
Childcare,ChildcareSchema,Apparel, ApparelSchema, Leisure,LeisureSchema)
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TEST_EMAIL = 'test@gmail.com'
TEST_PASSWORD = 'X4nmasXII!'

@pytest.fixture
def create_user(client):
    new_user = client.post('/v1/cost-of-living/auth/user',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return new_user

@pytest.fixture
def login(client, create_user):
    login = client.post('/v1/cost-of-living/auth/login',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD
        }))
    login_data = json.loads(login.get_data(as_text = True))
    return login_data

class TestUserResource:
    def test_user_post_no_user_no_admin(self,client):
        response = client.post('/v1/cost-of-living/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email' : TEST_EMAIL,
            'password': 'X4nmasXII!'
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'successfully registered'
        assert response.status_code == HttpStatus.created_201.value
        assert User.query.count() == 1
        assert User.query.first().admin == False
    
    def test_user_post_no_user_with_admin(self,client):
        response = client.post('/v1/cost-of-living/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email' : TEST_EMAIL,
            'password': 'X4nmasXII!',
            'admin': os.environ.get('ADMIN_KEY')
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'successfully registered with admin privileges'
        assert response.status_code == HttpStatus.created_201.value
        assert User.query.count() == 1
        assert User.query.first().admin == True

    def test_user_post_exist_user(self,client):
        post_response = client.post('/v1/cost-of-living/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
            }))
        second_post_response = client.post('/v1/cost-of-living/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email': TEST_EMAIL,
            'password': 'X4nmasXII!'
            }))
        second_post_response_data = json.loads(second_post_response.get_data(as_text = True))
        assert second_post_response_data['message'] == 'User already exists. Please log in'
        assert second_post_response.status_code == HttpStatus.conflict_409.value
        assert User.query.count() == 1

    def test_login_valid_user(self,client,create_user):
        response = client.post('/v1/cost-of-living/auth/login',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email' : TEST_EMAIL,
            'password': TEST_PASSWORD
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'successfully logged in'
        assert bool(response_data.get('auth_token')) == True
        assert response.status_code == HttpStatus.ok_200.value

    def test_login_invalid_user(self,client):
        response = client.post('/v1/cost-of-living/auth/login',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email' : TEST_EMAIL,
            'password': TEST_PASSWORD
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'User does not exist'
        assert response.status_code == HttpStatus.notfound_404.value

    def test_user_get_valid_token(self,client,create_user,login):
        get_response = client.get('/v1/cost-of-living/auth/user',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        print(get_response_data)
        assert get_response_data['data']['user_id'] == 1
        assert get_response_data['data']['email'] == TEST_EMAIL
        assert datetime.strptime(get_response_data['data']['creation_date'],'%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d') == date.today().strftime('%Y-%m-%d')
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_user_get_no_token(self,client):
        get_response = client.get('/v1/cost-of-living/auth/user',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer "})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['message'] == 'Provide a valid auth token'
        assert get_response.status_code == HttpStatus.forbidden_403.value

    def test_user_get_invalid_token(self,client):
        get_response = client.get('/v1/cost-of-living/auth/user', headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer invalid token"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['message'] == 'Invalid token. Please log in again'
        assert get_response.status_code == HttpStatus.unauthorized_401.value

    def test_user_get_expired_token(self,client,create_user,login):
        time.sleep(6)
        get_response = client.get('/v1/cost-of-living/auth/user',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['message'] == 'Signature expired. Please log in again'
        assert get_response.status_code == HttpStatus.unauthorized_401.value

    def test_user_get_malformed_bearer_token(self,client,create_user,login):
        get_response = client.get('/v1/cost-of-living/auth/user',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer{login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['message'] == 'Bearer token malformed'
        assert get_response.status_code == HttpStatus.unauthorized_401.value

    def test_logout_valid_token(self,client,create_user,login):
        response = client.post('/v1/cost-of-living/auth/logout', headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Successfully logged out'
        assert response.status_code == HttpStatus.ok_200.value
        assert BlacklistToken.query.count() == 1

    def test_logout_no_token(self,client):
        response = client.post('/v1/cost-of-living/auth/logout',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer "})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Provide a valid auth token'
        assert response.status_code == HttpStatus.forbidden_403.value
        assert BlacklistToken.query.count() == 0

    def test_logout_invalid_token(self,client):
        response = client.post('/v1/cost-of-living/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer invalid token"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Invalid token. Please log in again'
        assert response.status_code == HttpStatus.unauthorized_401.value
        assert BlacklistToken.query.count() == 0

    def test_logout_expired_token(self,client,create_user,login):
        time.sleep(6)
        response = client.post('/v1/cost-of-living/auth/logout', headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Signature expired. Please log in again'
        assert response.status_code == HttpStatus.unauthorized_401.value

    def test_logout_blacklisted_token(self,client,create_user,login):
        blacklist_token = BlacklistToken(token = login['auth_token'])
        blacklist_token.add(blacklist_token)
        assert BlacklistToken.query.count() == 1
        response = client.post('/v1/cost-of-living/auth/logout', headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Token blacklisted. Please log in again'
        assert response.status_code == HttpStatus.unauthorized_401.value
        assert BlacklistToken.query.count() == 1

    def test_logout_malformed_token(self,client,create_user,login):
        response = client.post('/v1/cost-of-living/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer{login['auth_token']}"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Bearer token malformed'
        assert response.status_code == HttpStatus.unauthorized_401.value
        assert BlacklistToken.query.count() == 0

    def test_reset_password_exist_user(self,client,create_user):
        response = client.post('/v1/cost-of-living/user/password_reset',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD
        }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Password reset successful'
        assert response.status_code == HttpStatus.ok_200.value

    def test_reset_password_no_user(self,client):
        response = client.post('/v1/cost-of-living/user/password_reset',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD
        }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'User does not exist'
        assert response.status_code == HttpStatus.unauthorized_401.value

def create_currency(client, abbreviation, usd_to_local_exchange_rate):
        response = client.post('/v1/cost-of-living/currencies',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'abbreviation': abbreviation,
            'usd_to_local_exchange_rate': usd_to_local_exchange_rate,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        return response

class TestCurrencyResource:
    def test_currency_post_new_currency(self,client):
        response = create_currency(client,'AUD',1.45)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['abbreviation'] == 'AUD'
        assert response_data['usd_to_local_exchange_rate'] == 1.45
        assert response.status_code == HttpStatus.created_201.value
        assert Currency.query.count() == 1
    
    def test_currency_post_new_currency_no_admin(self,client):
        response = client.post('/v1/cost-of-living/currencies',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'abbreviation': 'AUD',
        'usd_to_local_exchange_rate': 1.45
        }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'

    def test_currency_post_duplicated_currency(self,client):
        response = create_currency(client,'AUD',1.45)
        second_response = create_currency(client,'AUD',1.45)
        assert Currency.query.count() == 1
        assert second_response.status_code == HttpStatus.bad_request_400.value

    def test_currency_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        get_response = client.get('/v1/cost-of-living/currencies/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['abbreviation'] == 'AUD'
        assert get_response_data['usd_to_local_exchange_rate'] == 1.45
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_currency_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        get_response = client.get('/v1/cost-of-living/currencies/2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_currency_get_without_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        get_first_page_response = client.get('/v1/cost-of-living/currencies',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['results']) == 2
        assert get_first_page_response_data['results'][0]['abbreviation'] == 'AUD'
        assert get_first_page_response_data['results'][0]['usd_to_local_exchange_rate'] == 1.45
        assert get_first_page_response_data['results'][1]['abbreviation'] == 'CHF'
        assert get_first_page_response_data['results'][1]['usd_to_local_exchange_rate'] == 0.92
        assert get_first_page_response_data['count'] == 2
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/currencies?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/currencies?page=1'
        assert get_second_page_response_data['next'] == None
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_currency_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        patch_response = client.patch('/v1/cost-of-living/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'abbreviation': 'Aud',
        'usd_to_local_exchange_rate' : 1.50,
        'admin': os.environ.get('ADMIN_KEY')
        }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/currencies/1',
        headers = {'Content-Type': 'application/json',
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['abbreviation'] == 'Aud'
        assert get_response_data['usd_to_local_exchange_rate'] == 1.50
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_currency_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/currencies/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'abbreviation': 'Aud',
            'usd_to_local_exchange_rate' : 1.50,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert Currency.query.count() == 0
    
    def test_currency_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        patch_response = client.patch('/v1/cost-of-living/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'abbreviation': 'Aud',
        'usd_to_local_exchange_rate' : 1.50
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_currency_delete(self,client):
        create_currency(client,'AUD',1.45)
        delete_response = client.delete('/v1/cost-of-living/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert Currency.query.count() == 0
        assert delete_response.status_code == HttpStatus.no_content_204.value

    def test_currency_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Currency.query.count() == 0
    
    def test_currency_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        delete_response = client.delete('/v1/cost-of-living/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_location(client, country, city, abbreviation):
    response = client.post('/v1/cost-of-living/locations',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'country': country,
        'city': city,
        'abbreviation': abbreviation,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestLocationResource:
    def test_location_post_new_location_currency_exist(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        post_response = create_location(client,'Australia','Perth','AUD')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['country'] == 'Australia'
        assert post_response_data['city'] == 'Perth'
        assert post_response_data['currency']['id'] == 1
        assert post_response_data['currency']['abbreviation'] == 'AUD'
        assert post_response.status_code == HttpStatus.created_201.value
        assert Location.query.count() == 1
    
    def test_location_post_new_location_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        post_response = client.post('/v1/cost-of-living/locations',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'country': 'Australia',
        'city': 'Perth',
        'abbreviation': 'AUD',
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_location_post_new_location_currency_none(self,client):
        response = create_location(client,'Australia','Perth','AUD')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified currency doesnt exist in /currencies/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Location.query.count() == 0

    def test_location_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        get_response = client.get('/v1/cost-of-living/locations/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['country'] == 'Australia'
        assert get_response_data['city'] == 'Perth'
        assert get_response_data['currency']['id'] == 1
        assert get_response_data['currency']['abbreviation'] == 'AUD'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_location_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        get_response = client.get('/v1/cost-of-living/locations/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_location_get_without_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        get_first_page_response = client.get('/v1/cost-of-living/locations',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['locations']) == 2
        assert get_first_page_response_data['locations'][0]['country'] == 'Australia'
        assert get_first_page_response_data['locations'][0]['city'] == 'Perth'
        assert get_first_page_response_data['locations'][0]['currency']['id'] == 1
        assert get_first_page_response_data['locations'][0]['currency']['abbreviation'] == 'AUD'
        assert get_first_page_response_data['locations'][1]['country'] == 'Australia'
        assert get_first_page_response_data['locations'][1]['city'] == 'Melbourne'
        assert get_first_page_response_data['locations'][1]['currency']['id'] == 1
        assert get_first_page_response_data['locations'][1]['currency']['abbreviation'] == 'AUD'
        assert get_first_page_response_data['count'] == 2
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/locations?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/locations?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_location_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        delete_response = client.delete('/v1/cost-of-living/locations/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert Location.query.count() == 0

    def test_location_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/locations/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Location.query.count() == 0
    
    def test_location_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        delete_response = client.delete('/v1/cost-of-living/locations/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_home_purchase(client,property_location,price_per_sqm,mortgage_interest,city):
    response = client.post('/v1/cost-of-living/homepurchase',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': property_location,
        'price_per_sqm': price_per_sqm,
        'mortgage_interest': mortgage_interest,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestHomePurchaseResource:
    def test_home_purchase_post_home_purchase_location_exist(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['property_location'] == 'City Centre'
        assert post_response_data['price_per_sqm'] == 6339
        assert post_response_data['mortgage_interest'] == 5.09
        assert post_response_data['location']['id'] == 1
        assert post_response_data['location']['country'] == 'Australia'
        assert post_response_data['location']['city'] == 'Perth'
        assert post_response.status_code == HttpStatus.created_201.value
        assert HomePurchase.query.count() == 1
    
    def test_home_purchase_post_home_purchase_location_exist_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = client.post('/v1/cost-of-living/homepurchase',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'City Centre',
        'price_per_sqm': 6339,
        'mortgage_interest': 5.09,
        'city': 'Perth'
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_home_purchase_post_home_purchase_location_notexist(self,client):
        response = create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert HomePurchase.query.count() == 0

    def test_home_purchase_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        get_response = client.get('/v1/cost-of-living/homepurchase/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['property_location'] == 'City Centre'
        assert get_response_data['price_per_sqm'] == 6339
        assert get_response_data['mortgage_interest'] == 5.09
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        get_response = client.get('/v1/cost-of-living/homepurchase/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_home_purchase_get_country_city_abbreviation(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        create_home_purchase(client,'City Centre', 7252, 4.26, 'Melbourne')
        create_home_purchase(client,'City Centre', 14619, 4.25, 'Sydney')
        create_home_purchase(client,'City Centre', 20775, 1.92, 'Zurich')
        get_response = client.get('/v1/cost-of-living/homepurchase?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['price_per_sqm'] == 9191.55
        assert get_response_data[0]['mortgage_interest'] == 5.09
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_get_country_city_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        create_home_purchase(client,'City Centre', 7252, 4.26, 'Melbourne')
        create_home_purchase(client,'City Centre', 14619, 4.25, 'Sydney')
        create_home_purchase(client,'City Centre', 20775, 1.92, 'Zurich')
        get_response = client.get('/v1/cost-of-living/homepurchase?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['price_per_sqm'] == 6339
        assert get_response_data[0]['mortgage_interest'] == 5.09
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_get_country_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        create_home_purchase(client,'City Centre', 7252, 4.26, 'Melbourne')
        create_home_purchase(client,'City Centre', 14619, 4.25, 'Sydney')
        create_home_purchase(client,'City Centre', 20775, 1.92, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/currencies',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        get_first_page_response = client.get('/v1/cost-of-living/homepurchase?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['home purchase data']) == 3
        assert get_first_page_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][0]['price_per_sqm'] == 6339
        assert get_first_page_response_data['home purchase data'][0]['mortgage_interest'] == 5.09
        assert get_first_page_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][1]['price_per_sqm'] == 7252
        assert get_first_page_response_data['home purchase data'][1]['mortgage_interest'] == 4.26
        assert get_first_page_response_data['home purchase data'][1]['location']['id'] == 2
        assert get_first_page_response_data['home purchase data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['home purchase data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][2]['price_per_sqm'] == 14619
        assert get_first_page_response_data['home purchase data'][2]['mortgage_interest'] == 4.25
        assert get_first_page_response_data['home purchase data'][2]['location']['id'] == 3
        assert get_first_page_response_data['home purchase data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/homepurchase?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/homepurchase?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_get_country_abbreviation_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        create_home_purchase(client,'City Centre', 7252, 4.26, 'Melbourne')
        create_home_purchase(client,'City Centre', 14619, 4.25, 'Sydney')
        create_home_purchase(client,'City Centre', 20775, 1.92, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/homepurchase?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['home purchase data']) == 3
        assert get_first_page_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][0]['price_per_sqm'] == 9191.55
        assert get_first_page_response_data['home purchase data'][0]['mortgage_interest'] == 5.09
        assert get_first_page_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][1]['price_per_sqm'] == 10515.4
        assert get_first_page_response_data['home purchase data'][1]['mortgage_interest'] == 4.26
        assert get_first_page_response_data['home purchase data'][1]['location']['id'] == 2
        assert get_first_page_response_data['home purchase data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['home purchase data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][2]['price_per_sqm'] == 21197.55
        assert get_first_page_response_data['home purchase data'][2]['mortgage_interest'] == 4.25
        assert get_first_page_response_data['home purchase data'][2]['location']['id'] == 3
        assert get_first_page_response_data['home purchase data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/homepurchase?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/homepurchase?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_get_city_abbreviation_country_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        create_home_purchase(client,'City Centre', 7252, 4.26, 'Melbourne')
        create_home_purchase(client,'City Centre', 14619, 4.25, 'Sydney')
        create_home_purchase(client,'City Centre', 20775, 1.92, 'Zurich')
        get_response = client.get('/v1/cost-of-living/homepurchase?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['price_per_sqm'] == 9191.55
        assert get_response_data[0]['mortgage_interest'] == 5.09
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_get_country_none_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        create_home_purchase(client,'City Centre', 7252, 4.26, 'Melbourne')
        create_home_purchase(client,'City Centre', 14619, 4.25, 'Sydney')
        create_home_purchase(client,'City Centre', 20775, 1.92, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/homepurchase',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['home purchase data']) == 4
        assert get_first_page_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][0]['price_per_sqm'] == 6339
        assert get_first_page_response_data['home purchase data'][0]['mortgage_interest'] == 5.09
        assert get_first_page_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][1]['price_per_sqm'] == 7252
        assert get_first_page_response_data['home purchase data'][1]['mortgage_interest'] == 4.26
        assert get_first_page_response_data['home purchase data'][1]['location']['id'] == 2
        assert get_first_page_response_data['home purchase data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['home purchase data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][2]['price_per_sqm'] == 14619
        assert get_first_page_response_data['home purchase data'][2]['mortgage_interest'] == 4.25
        assert get_first_page_response_data['home purchase data'][2]['location']['id'] == 3
        assert get_first_page_response_data['home purchase data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['home purchase data'][3]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][3]['price_per_sqm'] == 20775
        assert get_first_page_response_data['home purchase data'][3]['mortgage_interest'] == 1.92
        assert get_first_page_response_data['home purchase data'][3]['location']['id'] == 4
        assert get_first_page_response_data['home purchase data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['home purchase data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/homepurchase?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/homepurchase?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_get_city_country_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        create_home_purchase(client,'City Centre', 7252, 4.26, 'Melbourne')
        create_home_purchase(client,'City Centre', 14619, 4.25, 'Sydney')
        create_home_purchase(client,'City Centre', 20775, 1.92, 'Zurich')
        get_response = client.get('/v1/cost-of-living/homepurchase?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['price_per_sqm'] == 6339
        assert get_response_data[0]['mortgage_interest'] == 5.09
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_get_abbreviation_country_none_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        create_home_purchase(client,'City Centre', 7252, 4.26, 'Melbourne')
        create_home_purchase(client,'City Centre', 14619, 4.25, 'Sydney')
        create_home_purchase(client,'City Centre', 20775, 1.92, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/homepurchase?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['home purchase data']) == 4
        assert get_first_page_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][0]['price_per_sqm'] == 9191.55
        assert get_first_page_response_data['home purchase data'][0]['mortgage_interest'] == 5.09
        assert get_first_page_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][1]['price_per_sqm'] == 10515.4
        assert get_first_page_response_data['home purchase data'][1]['mortgage_interest'] == 4.26
        assert get_first_page_response_data['home purchase data'][1]['location']['id'] == 2
        assert get_first_page_response_data['home purchase data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['home purchase data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][2]['price_per_sqm'] == 21197.55
        assert get_first_page_response_data['home purchase data'][2]['mortgage_interest'] == 4.25
        assert get_first_page_response_data['home purchase data'][2]['location']['id'] == 3
        assert get_first_page_response_data['home purchase data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['home purchase data'][3]['price_per_sqm'] == 30123.75
        assert get_first_page_response_data['home purchase data'][3]['mortgage_interest'] == 1.92
        assert get_first_page_response_data['home purchase data'][3]['location']['id'] == 4
        assert get_first_page_response_data['home purchase data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['home purchase data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/homepurchase?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/homepurchase?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_home_purchase(client,'City Centre', 6339.73, 5.09, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/homepurchase/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'property_location': 'Outside City Centre',
            'price_per_sqm': 7000,
            'mortgage_interest': 6.01,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/homepurchase/1',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['property_location'] == 'Outside City Centre'
        assert get_response_data['price_per_sqm'] == 7000
        assert get_response_data['mortgage_interest'] == 6.01
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_home_purchase_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/homepurchase/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'property_location': 'Outside City Centre',
            'price_per_sqm': 7000,
            'mortgage_interest': 6.01,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert HomePurchase.query.count() == 0
    
    def test_home_purchase_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_home_purchase(client,'City Centre', 6339.73, 5.09, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'price_per_sqm': 7000,
        'mortgage_interest': 6.01
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_home_purchase_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert HomePurchase.query.count() == 0

    def test_home_purchase_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert HomePurchase.query.count() == 0
    
    def test_home_purchase_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_home_purchase(client,'City Centre', 6339, 5.09, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_rent(client,property_location,bedrooms,monthly_price,city):
    response = client.post('/v1/cost-of-living/rent',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': property_location,
        'bedrooms': bedrooms,
        'monthly_price': monthly_price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestRentResource:
    def test_rent_post_new_rent_location_exist(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = create_rent(client,'City Centre', 1, 1642 , 'Perth')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['property_location'] == 'City Centre'
        assert post_response_data['bedrooms'] == 1
        assert post_response_data['monthly_price'] == 1642
        assert post_response_data['location']['id'] == 1
        assert post_response_data['location']['country'] == 'Australia'
        assert post_response_data['location']['city'] == 'Perth'
        assert post_response.status_code == HttpStatus.created_201.value
        assert Rent.query.count() == 1
    
    def test_rent_post_new_rent_location_exist_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = client.post('/v1/cost-of-living/rent',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'City Centre',
        'bedrooms': 1,
        'monthly_price': 1642,
        'city': 'Perth'
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_rent_post_new_rent_location_notexist(self,client):
        response = create_rent(client,'City Centre', 1, 1642, 'Perth')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Rent.query.count() == 0

    def test_rent_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        get_response = client.get('/v1/cost-of-living/rent/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['property_location'] == 'City Centre'
        assert get_response_data['bedrooms'] == 1
        assert get_response_data['monthly_price'] == 1642
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        get_response = client.get('/v1/cost-of-living/rent/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_rent_get_country_city_abbreviation(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        create_rent(client,'City Centre', 1, 1408, 'Melbourne')
        create_rent(client,'City Centre', 1, 1999, 'Sydney')
        create_rent(client,'City Centre', 1, 2263, 'Zurich')
        get_response = client.get('/v1/cost-of-living/rent?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['bedrooms'] == 1
        assert get_response_data[0]['monthly_price'] == 2380.9
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_country_city_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        create_rent(client,'City Centre', 1, 1408, 'Melbourne')
        create_rent(client,'City Centre', 1, 1999, 'Sydney')
        create_rent(client,'City Centre', 1, 2263, 'Zurich')
        get_response = client.get('/v1/cost-of-living/rent?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['bedrooms'] == 1
        assert get_response_data[0]['monthly_price'] == 1642
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_country_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        create_rent(client,'City Centre', 1, 1408, 'Melbourne')
        create_rent(client,'City Centre', 1, 1999, 'Sydney')
        create_rent(client,'City Centre', 1, 2263, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/rent?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['rental data']) == 3
        assert get_first_page_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][0]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][0]['monthly_price'] == 1408
        assert get_first_page_response_data['rental data'][0]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][1]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][1]['monthly_price'] == 1642
        assert get_first_page_response_data['rental data'][1]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][2]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][2]['monthly_price'] == 1999
        assert get_first_page_response_data['rental data'][2]['location']['id'] == 3
        assert get_first_page_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/rent?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/rent?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_country_abbreviation_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        create_rent(client,'City Centre', 1, 1408, 'Melbourne')
        create_rent(client,'City Centre', 1, 1999, 'Sydney')
        create_rent(client,'City Centre', 1, 2263, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/rent?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['rental data']) == 3
        assert get_first_page_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][0]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][0]['monthly_price'] == 2041.6
        assert get_first_page_response_data['rental data'][0]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][1]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][1]['monthly_price'] == 2380.9
        assert get_first_page_response_data['rental data'][1]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][2]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][2]['monthly_price'] == 2898.55
        assert get_first_page_response_data['rental data'][2]['location']['id'] == 3
        assert get_first_page_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/rent?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/rent?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_city_abbreviation_country_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        create_rent(client,'City Centre', 1, 1408, 'Melbourne')
        create_rent(client,'City Centre', 1, 1999, 'Sydney')
        create_rent(client,'City Centre', 1, 2263, 'Zurich')
        get_response = client.get('/v1/cost-of-living/rent?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['bedrooms'] == 1
        assert get_response_data[0]['monthly_price'] == 2380.9
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_country_none_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        create_rent(client,'City Centre', 1, 1408, 'Melbourne')
        create_rent(client,'City Centre', 1, 1999, 'Sydney')
        create_rent(client,'City Centre', 1, 2263, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/rent',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['rental data']) == 4
        assert get_first_page_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][0]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][0]['monthly_price'] == 1408
        assert get_first_page_response_data['rental data'][0]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][1]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][1]['monthly_price'] == 1642
        assert get_first_page_response_data['rental data'][1]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][2]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][2]['monthly_price'] == 1999
        assert get_first_page_response_data['rental data'][2]['location']['id'] == 3
        assert get_first_page_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['rental data'][3]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][3]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][3]['monthly_price'] == 2263
        assert get_first_page_response_data['rental data'][3]['location']['id'] == 4
        assert get_first_page_response_data['rental data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['rental data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/rent?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/rent?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_city_country_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        create_rent(client,'City Centre', 1, 1408, 'Melbourne')
        create_rent(client,'City Centre', 1, 1999, 'Sydney')
        create_rent(client,'City Centre', 1, 2263, 'Zurich')
        get_response = client.get('/v1/cost-of-living/rent?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['bedrooms'] == 1
        assert get_response_data[0]['monthly_price'] == 1642
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_abbreviation_country_none_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        create_rent(client,'City Centre', 1, 1408, 'Melbourne')
        create_rent(client,'City Centre', 1, 1999, 'Sydney')
        create_rent(client,'City Centre', 1, 2263, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/rent?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['rental data']) == 4
        assert get_first_page_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][0]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][0]['monthly_price'] == 2041.6
        assert get_first_page_response_data['rental data'][0]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][1]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][1]['monthly_price'] == 2380.9
        assert get_first_page_response_data['rental data'][1]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][2]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][2]['monthly_price'] == 2898.55
        assert get_first_page_response_data['rental data'][2]['location']['id'] == 3
        assert get_first_page_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['rental data'][3]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][3]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][3]['monthly_price'] == 3281.35
        assert get_first_page_response_data['rental data'][3]['location']['id'] == 4
        assert get_first_page_response_data['rental data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['rental data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/rent?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/rent?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_rent_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/rent/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'property_location': 'Outside City Centre',
            'bedrooms': 3,
            'monthly_price': 2526,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/rent/1',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['property_location'] == 'Outside City Centre'
        assert get_response_data['bedrooms'] == 3
        assert get_response_data['monthly_price'] == 2526
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/rent/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'property_location': 'Outside City Centre',
            'bedrooms': 3,
            'monthly_price': 2526.62,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert Rent.query.count() == 0
    
    def test_rent_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'price_per_sqm': 7000,
        'mortgage_interest': 6.01
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_rent_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642.43, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert Rent.query.count() == 0

    def test_rent_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Rent.query.count() == 0
    
    def test_rent_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642.43, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_utilities(client,utility,monthly_price,city):
    response = client.post('/v1/cost-of-living/utilities',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'utility': utility,
        'monthly_price': monthly_price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestUtilitiesResource:
    def test_utilities_post_utilities_location_exist(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert post_response_data['monthly_price'] == 210
        assert post_response_data['location']['id'] == 1
        assert post_response_data['location']['country'] == 'Australia'
        assert post_response_data['location']['city'] == 'Perth'
        assert post_response.status_code == HttpStatus.created_201.value
        assert Utilities.query.count() == 1
    
    def test_utilities_post_utilities_location_exist_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = client.post('/v1/cost-of-living/utilities',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'utility': 'Electricity, Heating, Cooling, Water and Garbage',
        'monthly_price': 210,
        'city': 'Perth'
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_utilities_post_utilities_location_notexist(self,client):
        response = create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Utilities.query.count() == 0

    def test_utilities_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        get_response = client.get('/v1/cost-of-living/utilities/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_response_data['monthly_price'] == 210
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        get_response = client.get('/v1/cost-of-living/utilities/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_utilities_get_country_city_abbreviation(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
        get_response = client.get('/v1/cost-of-living/utilities?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_response_data[0]['monthly_price'] == 304.5
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_country_city_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
        get_response = client.get('/v1/cost-of-living/utilities?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_response_data[0]['monthly_price'] == 210
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_country_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/utilities?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['utilities']) == 3
        assert get_first_page_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][0]['monthly_price'] == 172
        assert get_first_page_response_data['utilities'][0]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][1]['monthly_price'] == 174
        assert get_first_page_response_data['utilities'][1]['location']['id'] == 3
        assert get_first_page_response_data['utilities'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['utilities'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][2]['monthly_price'] == 210
        assert get_first_page_response_data['utilities'][2]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/utilities?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/utilities?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_country_abbreviation_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/utilities?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['utilities']) == 3
        assert get_first_page_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][0]['monthly_price'] == 249.4
        assert get_first_page_response_data['utilities'][0]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][1]['monthly_price'] == 252.3
        assert get_first_page_response_data['utilities'][1]['location']['id'] == 3
        assert get_first_page_response_data['utilities'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['utilities'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][2]['monthly_price'] == 304.5
        assert get_first_page_response_data['utilities'][2]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/utilities?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/utilities?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_city_abbreviation_country_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
        get_response = client.get('/v1/cost-of-living/utilities?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_response_data[0]['monthly_price'] == 304.5
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_country_none_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/utilities',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['utilities']) == 4
        assert get_first_page_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][0]['monthly_price'] == 172
        assert get_first_page_response_data['utilities'][0]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][1]['monthly_price'] == 174
        assert get_first_page_response_data['utilities'][1]['location']['id'] == 3
        assert get_first_page_response_data['utilities'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['utilities'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][2]['monthly_price'] == 210
        assert get_first_page_response_data['utilities'][2]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][3]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][3]['monthly_price'] == 273
        assert get_first_page_response_data['utilities'][3]['location']['id'] == 4
        assert get_first_page_response_data['utilities'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['utilities'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/utilities?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/utilities?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_city_country_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
        get_response = client.get('/v1/cost-of-living/utilities?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_response_data[0]['monthly_price'] == 210
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_abbreviation_country_none_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 172, 'Melbourne')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 174, 'Sydney')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 273, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/utilities?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['utilities']) == 4
        assert get_first_page_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][0]['monthly_price'] == 249.4
        assert get_first_page_response_data['utilities'][0]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][1]['monthly_price'] == 252.3
        assert get_first_page_response_data['utilities'][1]['location']['id'] == 3
        assert get_first_page_response_data['utilities'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['utilities'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][2]['monthly_price'] == 304.5
        assert get_first_page_response_data['utilities'][2]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][3]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage'
        assert get_first_page_response_data['utilities'][3]['monthly_price'] == 395.85
        assert get_first_page_response_data['utilities'][3]['location']['id'] == 4
        assert get_first_page_response_data['utilities'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['utilities'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/utilities?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/utilities?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_utilities_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/utilities/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'utility': 'Internet',
            'monthly_price': 55,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/utilities/1',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['utility'] == 'Internet'
        assert get_response_data['monthly_price'] == 55
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/utilities/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'utility': 'Internet',
            'monthly_price': 55,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert Utilities.query.count() == 0
    
    def test_utilities_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'price_per_sqm': 7000,
        'mortgage_interest': 6.01
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_utilities_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert Utilities.query.count() == 0

    def test_utilities_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Utilities.query.count() == 0
    
    def test_utilities_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_transportation(client,type,price,city):
    response = client.post('/v1/cost-of-living/transportation',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': type,
        'price': price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestTransportationResource:
    def test_transportation_post_transportation_location_exist(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['type'] == 'Monthly Public Transportation Pass'
        assert post_response_data['price'] == 103
        assert post_response_data['location']['id'] == 1
        assert post_response_data['location']['country'] == 'Australia'
        assert post_response_data['location']['city'] == 'Perth'
        assert post_response.status_code == HttpStatus.created_201.value
        assert Transportation.query.count() == 1
    
    def test_transportation_post_transportation_location_exist_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = client.post('/v1/cost-of-living/transportation',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': 'Monthly Public Transportation Pass',
        'price': 103,
        'city': 'Perth'
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_transportation_post_transportation_location_notexist(self,client):
        response = create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Transportation.query.count() == 0

    def test_transportation_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        get_response = client.get('/v1/cost-of-living/transportation/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['type'] == 'Monthly Public Transportation Pass'
        assert get_response_data['price'] == 103
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        get_response = client.get('/v1/cost-of-living/transportation/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_transportation_get_country_city_abbreviation(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        create_transportation(client,'Monthly Public Transportation Pass', 112, 'Melbourne')
        create_transportation(client,'Monthly Public Transportation Pass', 150, 'Sydney')
        create_transportation(client,'Monthly Public Transportation Pass', 102, 'Zurich')
        get_response = client.get('/v1/cost-of-living/transportation?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['type'] == 'Monthly Public Transportation Pass'
        assert get_response_data[0]['price'] == 149.35
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_country_city_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        create_transportation(client,'Monthly Public Transportation Pass', 112, 'Melbourne')
        create_transportation(client,'Monthly Public Transportation Pass', 150, 'Sydney')
        create_transportation(client,'Monthly Public Transportation Pass', 102, 'Zurich')
        get_response = client.get('/v1/cost-of-living/transportation?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['type'] == 'Monthly Public Transportation Pass'
        assert get_response_data[0]['price'] == 103
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_country_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        create_transportation(client,'Monthly Public Transportation Pass', 112, 'Melbourne')
        create_transportation(client,'Monthly Public Transportation Pass', 150, 'Sydney')
        create_transportation(client,'Monthly Public Transportation Pass', 102, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/transportation?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['transportation data']) == 3
        assert get_first_page_response_data['transportation data'][0]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][0]['price'] == 103
        assert get_first_page_response_data['transportation data'][0]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][1]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][1]['price'] == 112
        assert get_first_page_response_data['transportation data'][1]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['transportation data'][2]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][2]['price'] == 150
        assert get_first_page_response_data['transportation data'][2]['location']['id'] == 3
        assert get_first_page_response_data['transportation data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/transportation?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/transportation?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_country_abbreviation_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        create_transportation(client,'Monthly Public Transportation Pass', 112, 'Melbourne')
        create_transportation(client,'Monthly Public Transportation Pass', 150, 'Sydney')
        create_transportation(client,'Monthly Public Transportation Pass', 102, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/transportation?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['transportation data']) == 3
        assert get_first_page_response_data['transportation data'][0]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][0]['price'] == 149.35
        assert get_first_page_response_data['transportation data'][0]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][1]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][1]['price'] == 162.4
        assert get_first_page_response_data['transportation data'][1]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['transportation data'][2]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][2]['price'] == 217.5
        assert get_first_page_response_data['transportation data'][2]['location']['id'] == 3
        assert get_first_page_response_data['transportation data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/transportation?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/transportation?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_city_abbreviation_country_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        create_transportation(client,'Monthly Public Transportation Pass', 112, 'Melbourne')
        create_transportation(client,'Monthly Public Transportation Pass', 150, 'Sydney')
        create_transportation(client,'Monthly Public Transportation Pass', 102, 'Zurich')
        get_response = client.get('/v1/cost-of-living/transportation?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['type'] == 'Monthly Public Transportation Pass'
        assert get_response_data[0]['price'] == 149.35
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_country_none_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        create_transportation(client,'Monthly Public Transportation Pass', 112, 'Melbourne')
        create_transportation(client,'Monthly Public Transportation Pass', 150, 'Sydney')
        create_transportation(client,'Monthly Public Transportation Pass', 102, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/transportation',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['transportation data']) == 4
        assert get_first_page_response_data['transportation data'][0]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][0]['price'] == 102
        assert get_first_page_response_data['transportation data'][0]['location']['id'] == 4
        assert get_first_page_response_data['transportation data'][0]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['transportation data'][0]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['transportation data'][1]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][1]['price'] == 103
        assert get_first_page_response_data['transportation data'][1]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][2]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][2]['price'] == 112
        assert get_first_page_response_data['transportation data'][2]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['transportation data'][3]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][3]['price'] == 150
        assert get_first_page_response_data['transportation data'][3]['location']['id'] == 3
        assert get_first_page_response_data['transportation data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][3]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/transportation?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/transportation?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_city_country_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        create_transportation(client,'Monthly Public Transportation Pass', 112, 'Melbourne')
        create_transportation(client,'Monthly Public Transportation Pass', 150, 'Sydney')
        create_transportation(client,'Monthly Public Transportation Pass', 102, 'Zurich')
        get_response = client.get('/v1/cost-of-living/transportation?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['type'] == 'Monthly Public Transportation Pass'
        assert get_response_data[0]['price'] == 103
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_abbreviation_country_none_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        create_transportation(client,'Monthly Public Transportation Pass', 112, 'Melbourne')
        create_transportation(client,'Monthly Public Transportation Pass', 150, 'Sydney')
        create_transportation(client,'Monthly Public Transportation Pass', 102, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/transportation?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['transportation data']) == 4
        assert get_first_page_response_data['transportation data'][0]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][0]['price'] == 147.9
        assert get_first_page_response_data['transportation data'][0]['location']['id'] == 4
        assert get_first_page_response_data['transportation data'][0]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['transportation data'][0]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['transportation data'][1]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][1]['price'] == 149.35
        assert get_first_page_response_data['transportation data'][1]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][2]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][2]['price'] == 162.4
        assert get_first_page_response_data['transportation data'][2]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['transportation data'][3]['type'] == 'Monthly Public Transportation Pass'
        assert get_first_page_response_data['transportation data'][3]['price'] == 217.5
        assert get_first_page_response_data['transportation data'][3]['location']['id'] == 3
        assert get_first_page_response_data['transportation data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][3]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/transportation?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/transportation?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_transportation_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/transportation/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'type': 'One-Way Ticket',
            'price': 2.76,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/transportation/1',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['type'] == 'One-Way Ticket'
        assert get_response_data['price'] == 2.76
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/transportation/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'type': 'One-Way Ticket',
            'price': 2.76,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert Transportation.query.count() == 0

    def test_transportation_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': 'One-Way Ticket',
        'price': 2.76,
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_transportation_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert Transportation.query.count() == 0

    def test_transportation_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Transportation.query.count() == 0
    
    def test_transportation_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_foodbeverage(client,item_category,purchase_point,item,price,city):
    response = client.post('/v1/cost-of-living/foodbeverage',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item_category': item_category,
        'purchase_point': purchase_point,
        'item': item,
        'price': price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestFoodBeverageResource:
    def test_foodbeverage_post_foodbeverage_location_exist(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['item_category'] == 'Beverage'
        assert post_response_data['purchase_point'] == 'Supermarket'
        assert post_response_data['item'] == 'Milk 1L'
        assert post_response_data['price'] == 1.77
        assert post_response_data['location']['id'] == 1
        assert post_response_data['location']['country'] == 'Australia'
        assert post_response_data['location']['city'] == 'Perth'
        assert post_response.status_code == HttpStatus.created_201.value
        assert FoodBeverage.query.count() == 1
    
    def test_foodbeverage_post_foodbeverage_location_exist_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = client.post('/v1/cost-of-living/foodbeverage',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item_category': 'Beverage',
        'purchase_point': 'Supermarket',
        'item': 'Milk 1L',
        'price': 1.77,
        'city': 'Perth'
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_foodbeverage_post_foodbeverage_location_notexist(self,client):
        response = create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert FoodBeverage.query.count() == 0

    def test_foodbeverage_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        get_response = client.get('/v1/cost-of-living/foodbeverage/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['item_category'] == 'Beverage'
        assert get_response_data['purchase_point'] == 'Supermarket'
        assert get_response_data['item'] == 'Milk 1L'
        assert get_response_data['price'] == 1.77
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        get_response = client.get('/v1/cost-of-living/foodbeverage/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_foodbeverage_get_country_city_abbreviation(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.50, 'Melbourne')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.62, 'Sydney')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.80, 'Zurich')
        get_response = client.get('/v1/cost-of-living/foodbeverage?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item_category'] == 'Beverage'
        assert get_response_data[0]['purchase_point'] == 'Supermarket'
        assert get_response_data[0]['item'] == 'Milk 1L'
        assert get_response_data[0]['price'] == 2.57
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_country_city_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.50, 'Melbourne')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.62, 'Sydney')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.80, 'Zurich')
        get_response = client.get('/v1/cost-of-living/foodbeverage?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item_category'] == 'Beverage'
        assert get_response_data[0]['purchase_point'] == 'Supermarket'
        assert get_response_data[0]['item'] == 'Milk 1L'
        assert get_response_data[0]['price'] == 1.77
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_country_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.50, 'Melbourne')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.62, 'Sydney')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.80, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/foodbeverage?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['food and beverage data']) == 3
        assert get_first_page_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][0]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][0]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][0]['price'] == 1.50
        assert get_first_page_response_data['food and beverage data'][0]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][1]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][1]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][1]['price'] == 1.62
        assert get_first_page_response_data['food and beverage data'][1]['location']['id'] == 3
        assert get_first_page_response_data['food and beverage data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][2]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][2]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][2]['price'] == 1.77
        assert get_first_page_response_data['food and beverage data'][2]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/foodbeverage?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/foodbeverage?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_country_abbreviation_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.50, 'Melbourne')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.62, 'Sydney')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.80, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/foodbeverage?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['food and beverage data']) == 3
        assert get_first_page_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][0]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][0]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][0]['price'] == 2.17
        assert get_first_page_response_data['food and beverage data'][0]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][1]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][1]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][1]['price'] == 2.35
        assert get_first_page_response_data['food and beverage data'][1]['location']['id'] == 3
        assert get_first_page_response_data['food and beverage data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][2]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][2]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][2]['price'] == 2.57
        assert get_first_page_response_data['food and beverage data'][2]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/foodbeverage?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/foodbeverage?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_city_abbreviation_country_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.50, 'Melbourne')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.62, 'Sydney')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.80, 'Zurich')
        get_response = client.get('/v1/cost-of-living/foodbeverage?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item_category'] == 'Beverage'
        assert get_response_data[0]['purchase_point'] == 'Supermarket'
        assert get_response_data[0]['item'] == 'Milk 1L'
        assert get_response_data[0]['price'] == 2.57
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_country_none_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.50, 'Melbourne')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.62, 'Sydney')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.80, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/foodbeverage',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['food and beverage data']) == 4
        assert get_first_page_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][0]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][0]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][0]['price'] == 1.50
        assert get_first_page_response_data['food and beverage data'][0]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][1]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][1]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][1]['price'] == 1.62
        assert get_first_page_response_data['food and beverage data'][1]['location']['id'] == 3
        assert get_first_page_response_data['food and beverage data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][2]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][2]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][2]['price'] == 1.77
        assert get_first_page_response_data['food and beverage data'][2]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][3]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][3]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][3]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][3]['price'] == 1.80
        assert get_first_page_response_data['food and beverage data'][3]['location']['id'] == 4
        assert get_first_page_response_data['food and beverage data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['food and beverage data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/foodbeverage?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/foodbeverage?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_city_country_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.50, 'Melbourne')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.62, 'Sydney')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.80, 'Zurich')
        get_response = client.get('/v1/cost-of-living/foodbeverage?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item_category'] == 'Beverage'
        assert get_response_data[0]['purchase_point'] == 'Supermarket'
        assert get_response_data[0]['item'] == 'Milk 1L'
        assert get_response_data[0]['price'] == 1.77
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_abbreviation_country_none_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.50, 'Melbourne')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.62, 'Sydney')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.80, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/foodbeverage?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['food and beverage data']) == 4
        assert get_first_page_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][0]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][0]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][0]['price'] == 2.17
        assert get_first_page_response_data['food and beverage data'][0]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][0]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][1]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][1]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][1]['price'] == 2.35
        assert get_first_page_response_data['food and beverage data'][1]['location']['id'] == 3
        assert get_first_page_response_data['food and beverage data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][2]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][2]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][2]['price'] == 2.57
        assert get_first_page_response_data['food and beverage data'][2]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][3]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][3]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][3]['item'] == 'Milk 1L'
        assert get_first_page_response_data['food and beverage data'][3]['price'] == 2.61
        assert get_first_page_response_data['food and beverage data'][3]['location']['id'] == 4
        assert get_first_page_response_data['food and beverage data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['food and beverage data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/foodbeverage?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/foodbeverage?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/foodbeverage/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'item_category': 'Food',
            'purchase_point': 'Restaurant',
            'item': 'McMeal',
            'price': 10.24,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/foodbeverage/1',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['item_category'] == 'Food'
        assert get_response_data['purchase_point'] == 'Restaurant'
        assert get_response_data['item'] == 'McMeal'
        assert get_response_data['price'] == 10.24
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/foodbeverage/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'item_category': 'Food',
            'purchase_point': 'Restaurant',
            'item': 'McMeal',
            'price': 10.24,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert FoodBeverage.query.count() == 0
    
    def test_foodbeverage_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item_category': 'Food',
        'purchase_point': 'Restaurant',
        'item': 'McMeal',
        'price': 10.24
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_foodbeverage_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert FoodBeverage.query.count() == 0

    def test_foodbeverage_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert FoodBeverage.query.count() == 0
    
    def test_foodbeverage_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_childcare(client,type,annual_price,city):
    response = client.post('/v1/cost-of-living/childcare',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': type,
        'annual_price': annual_price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestChildcareResource:
    def test_childcare_post_childcare_location_exist(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = create_childcare(client,'Preschool', 19632, 'Perth')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['type'] == 'Preschool'
        assert post_response_data['annual_price'] == 19632
        assert post_response_data['location']['id'] == 1
        assert post_response_data['location']['country'] == 'Australia'
        assert post_response_data['location']['city'] == 'Perth'
        assert post_response.status_code == HttpStatus.created_201.value
        assert Childcare.query.count() == 1
    
    def test_childcare_post_childcare_location_exist_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = client.post('/v1/cost-of-living/childcare',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': 'Preschool',
        'annual_price': 19632,
        'city': 'Perth',
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_childcare_post_childcare_location_notexist(self,client):
        response = create_childcare(client,'Preschool', 19632, 'Perth')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Childcare.query.count() == 0

    def test_childcare_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        get_response = client.get('/v1/cost-of-living/childcare/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['type'] == 'Preschool'
        assert get_response_data['annual_price'] == 19632
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        get_response = client.get('/v1/cost-of-living/childcare/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_childcare_get_country_city_abbreviation(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_childcare(client,'Preschool', 19632, 'Perth')
        create_childcare(client,'Preschool', 21012, 'Melbourne')
        create_childcare(client,'Preschool', 20376, 'Sydney')
        create_childcare(client,'Preschool', 35616, 'Zurich')
        get_response = client.get('/v1/cost-of-living/childcare?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['type'] == 'Preschool'
        assert get_response_data[0]['annual_price'] == 28466.4
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_country_city_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_childcare(client,'Preschool', 19632, 'Perth')
        create_childcare(client,'Preschool', 21012, 'Melbourne')
        create_childcare(client,'Preschool', 20376, 'Sydney')
        create_childcare(client,'Preschool', 35616, 'Zurich')
        get_response = client.get('/v1/cost-of-living/childcare?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['type'] == 'Preschool'
        assert get_response_data[0]['annual_price'] == 19632
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_country_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_childcare(client,'Preschool', 19632, 'Perth')
        create_childcare(client,'Preschool', 21012, 'Melbourne')
        create_childcare(client,'Preschool', 20376, 'Sydney')
        create_childcare(client,'Preschool', 35616, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/childcare?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['childcare data']) == 3
        assert get_first_page_response_data['childcare data'][0]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][0]['annual_price'] == 19632
        assert get_first_page_response_data['childcare data'][0]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][1]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][1]['annual_price'] == 20376
        assert get_first_page_response_data['childcare data'][1]['location']['id'] == 3
        assert get_first_page_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['childcare data'][2]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][2]['annual_price'] == 21012
        assert get_first_page_response_data['childcare data'][2]['location']['id'] == 2
        assert get_first_page_response_data['childcare data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/childcare?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/childcare?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_country_abbreviation_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_childcare(client,'Preschool', 19632, 'Perth')
        create_childcare(client,'Preschool', 21012, 'Melbourne')
        create_childcare(client,'Preschool', 20376, 'Sydney')
        create_childcare(client,'Preschool', 35616, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/childcare?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['childcare data']) == 3
        assert get_first_page_response_data['childcare data'][0]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][0]['annual_price'] == 28466.4
        assert get_first_page_response_data['childcare data'][0]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][1]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][1]['annual_price'] == 29545.2
        assert get_first_page_response_data['childcare data'][1]['location']['id'] == 3
        assert get_first_page_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['childcare data'][2]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][2]['annual_price'] == 30467.4
        assert get_first_page_response_data['childcare data'][2]['location']['id'] == 2
        assert get_first_page_response_data['childcare data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/childcare?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/childcare?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_city_abbreviation_country_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_childcare(client,'Preschool', 19632, 'Perth')
        create_childcare(client,'Preschool', 21012, 'Melbourne')
        create_childcare(client,'Preschool', 20376, 'Sydney')
        create_childcare(client,'Preschool', 35616, 'Zurich')
        get_response = client.get('/v1/cost-of-living/childcare?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['type'] == 'Preschool'
        assert get_response_data[0]['annual_price'] == 28466.4
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_country_none_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_childcare(client,'Preschool', 19632, 'Perth')
        create_childcare(client,'Preschool', 21012, 'Melbourne')
        create_childcare(client,'Preschool', 20376, 'Sydney')
        create_childcare(client,'Preschool', 35616, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/childcare',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['childcare data']) == 4
        assert get_first_page_response_data['childcare data'][0]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][0]['annual_price'] == 19632
        assert get_first_page_response_data['childcare data'][0]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][1]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][1]['annual_price'] == 20376
        assert get_first_page_response_data['childcare data'][1]['location']['id'] == 3
        assert get_first_page_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['childcare data'][2]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][2]['annual_price'] == 21012
        assert get_first_page_response_data['childcare data'][2]['location']['id'] == 2
        assert get_first_page_response_data['childcare data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['childcare data'][3]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][3]['annual_price'] == 35616
        assert get_first_page_response_data['childcare data'][3]['location']['id'] == 4
        assert get_first_page_response_data['childcare data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['childcare data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/childcare?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/childcare?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_city_country_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_childcare(client,'Preschool', 19632, 'Perth')
        create_childcare(client,'Preschool', 21012, 'Melbourne')
        create_childcare(client,'Preschool', 20376, 'Sydney')
        create_childcare(client,'Preschool', 35616, 'Zurich')
        get_response = client.get('/v1/cost-of-living/childcare?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['type'] == 'Preschool'
        assert get_response_data[0]['annual_price'] == 19632
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_abbreviation_country_none_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_childcare(client,'Preschool', 19632, 'Perth')
        create_childcare(client,'Preschool', 21012, 'Melbourne')
        create_childcare(client,'Preschool', 20376, 'Sydney')
        create_childcare(client,'Preschool', 35616, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/childcare?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['childcare data']) == 4
        assert get_first_page_response_data['childcare data'][0]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][0]['annual_price'] == 28466.4
        assert get_first_page_response_data['childcare data'][0]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][1]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][1]['annual_price'] == 29545.2
        assert get_first_page_response_data['childcare data'][1]['location']['id'] == 3
        assert get_first_page_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['childcare data'][2]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][2]['annual_price'] == 30467.4
        assert get_first_page_response_data['childcare data'][2]['location']['id'] == 2
        assert get_first_page_response_data['childcare data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['childcare data'][3]['type'] == 'Preschool'
        assert get_first_page_response_data['childcare data'][3]['annual_price'] == 51643.2
        assert get_first_page_response_data['childcare data'][3]['location']['id'] == 4
        assert get_first_page_response_data['childcare data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['childcare data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/childcare?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/childcare?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_childcare_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/childcare/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'type': 'International Primary School',
            'annual_price': 15547.56,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/childcare/1',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['type'] == 'International Primary School'
        assert get_response_data['annual_price'] == 15547.56
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/childcare/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'type': 'International Primary School',
            'annual_price': 15547.56,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert Childcare.query.count() == 0
    
    def test_childcare_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item_category': 'Food',
        'purchase_point': 'Restaurant',
        'item': 'McMeal',
        'price': 10.24
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_childcare_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert Childcare.query.count() == 0

    def test_childcare_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Childcare.query.count() == 0
    
    def test_childcare_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_apparel(client,item,price,city):
    response = client.post('/v1/cost-of-living/apparel',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item': item,
        'price': price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestApparelResource:
    def test_apparel_post_apparel_location_exist(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['item'] == 'Levis Pair of Jeans'
        assert post_response_data['price'] == 77
        assert post_response_data['location']['id'] == 1
        assert post_response_data['location']['country'] == 'Australia'
        assert post_response_data['location']['city'] == 'Perth'
        assert post_response.status_code == HttpStatus.created_201.value
        assert Apparel.query.count() == 1
    
    def test_apparel_post_apparel_location_exist_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = client.post('/v1/cost-of-living/apparel',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item': 'Levis Pair of Jeans',
        'price': 77,
        'city': 'Perth',
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_apparel_post_apparel_location_notexist(self,client):
        response = create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Apparel.query.count() == 0

    def test_apparel_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        get_response = client.get('/v1/cost-of-living/apparel/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['item'] == 'Levis Pair of Jeans'
        assert get_response_data['price'] == 77
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        get_response = client.get('/v1/cost-of-living/apparel/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_apparel_get_country_city_abbreviation(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        create_apparel(client,'Levis Pair of Jeans', 84, 'Melbourne')
        create_apparel(client,'Levis Pair of Jeans', 83, 'Sydney')
        create_apparel(client,'Levis Pair of Jeans', 114, 'Zurich')
        get_response = client.get('/v1/cost-of-living/apparel?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item'] == 'Levis Pair of Jeans'
        assert get_response_data[0]['price'] == 111.65
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_country_city_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        create_apparel(client,'Levis Pair of Jeans', 84, 'Melbourne')
        create_apparel(client,'Levis Pair of Jeans', 83, 'Sydney')
        create_apparel(client,'Levis Pair of Jeans', 114, 'Zurich')
        get_response = client.get('/v1/cost-of-living/apparel?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item'] == 'Levis Pair of Jeans'
        assert get_response_data[0]['price'] == 77
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_country_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        create_apparel(client,'Levis Pair of Jeans', 84, 'Melbourne')
        create_apparel(client,'Levis Pair of Jeans', 83, 'Sydney')
        create_apparel(client,'Levis Pair of Jeans', 114, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/apparel?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['apparel data']) == 3
        assert get_first_page_response_data['apparel data'][0]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][0]['price'] == 77
        assert get_first_page_response_data['apparel data'][0]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][1]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][1]['price'] == 83
        assert get_first_page_response_data['apparel data'][1]['location']['id'] == 3
        assert get_first_page_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['apparel data'][2]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][2]['price'] == 84
        assert get_first_page_response_data['apparel data'][2]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/apparel?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/apparel?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_country_abbreviation_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        create_apparel(client,'Levis Pair of Jeans', 84, 'Melbourne')
        create_apparel(client,'Levis Pair of Jeans', 83, 'Sydney')
        create_apparel(client,'Levis Pair of Jeans', 114, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/apparel?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['apparel data']) == 3
        assert get_first_page_response_data['apparel data'][0]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][0]['price'] == 111.65
        assert get_first_page_response_data['apparel data'][0]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][1]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][1]['price'] == 120.35
        assert get_first_page_response_data['apparel data'][1]['location']['id'] == 3
        assert get_first_page_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['apparel data'][2]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][2]['price'] == 121.8
        assert get_first_page_response_data['apparel data'][2]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/apparel?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/apparel?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_city_abbreviation_country_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        create_apparel(client,'Levis Pair of Jeans', 84, 'Melbourne')
        create_apparel(client,'Levis Pair of Jeans', 83, 'Sydney')
        create_apparel(client,'Levis Pair of Jeans', 114, 'Zurich')
        get_response = client.get('/v1/cost-of-living/apparel?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item'] == 'Levis Pair of Jeans'
        assert get_response_data[0]['price'] == 111.65
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_country_none_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        create_apparel(client,'Levis Pair of Jeans', 84, 'Melbourne')
        create_apparel(client,'Levis Pair of Jeans', 83, 'Sydney')
        create_apparel(client,'Levis Pair of Jeans', 114, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/apparel',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['apparel data']) == 4
        assert get_first_page_response_data['apparel data'][0]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][0]['price'] == 77
        assert get_first_page_response_data['apparel data'][0]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][1]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][1]['price'] == 83
        assert get_first_page_response_data['apparel data'][1]['location']['id'] == 3
        assert get_first_page_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['apparel data'][2]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][2]['price'] == 84
        assert get_first_page_response_data['apparel data'][2]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['apparel data'][3]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][3]['price'] == 114
        assert get_first_page_response_data['apparel data'][3]['location']['id'] == 4
        assert get_first_page_response_data['apparel data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['apparel data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/apparel?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/apparel?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_city_country_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        create_apparel(client,'Levis Pair of Jeans', 84, 'Melbourne')
        create_apparel(client,'Levis Pair of Jeans', 83, 'Sydney')
        create_apparel(client,'Levis Pair of Jeans', 114, 'Zurich')
        get_response = client.get('/v1/cost-of-living/apparel?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item'] == 'Levis Pair of Jeans'
        assert get_response_data[0]['price'] == 77
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_abbreviation_country_none_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        create_apparel(client,'Levis Pair of Jeans', 84, 'Melbourne')
        create_apparel(client,'Levis Pair of Jeans', 83, 'Sydney')
        create_apparel(client,'Levis Pair of Jeans', 114, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/apparel?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['apparel data']) == 4
        assert get_first_page_response_data['apparel data'][0]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][0]['price'] == 111.65
        assert get_first_page_response_data['apparel data'][0]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][1]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][1]['price'] == 120.35
        assert get_first_page_response_data['apparel data'][1]['location']['id'] == 3
        assert get_first_page_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][1]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['apparel data'][2]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][2]['price'] == 121.8
        assert get_first_page_response_data['apparel data'][2]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][2]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['apparel data'][3]['item'] == 'Levis Pair of Jeans'
        assert get_first_page_response_data['apparel data'][3]['price'] == 165.3
        assert get_first_page_response_data['apparel data'][3]['location']['id'] == 4
        assert get_first_page_response_data['apparel data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['apparel data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/apparel?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/apparel?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_apparel_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/apparel/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'item': 'Mens Leather Business Shoes',
            'price': 194,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/apparel/1',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['item'] == 'Mens Leather Business Shoes'
        assert get_response_data['price'] == 194
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/apparel/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'item': 'Mens Leather Business Shoes',
            'price': 194,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert Apparel.query.count() == 0
    
    def test_apparel_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item': 'Mens Leather Business Shoes',
        'price': 194
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_apparel_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert Apparel.query.count() == 0

    def test_apparel_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Apparel.query.count() == 0
    
    def test_apparel_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

def create_leisure(client,activity,price,city):
    response = client.post('/v1/cost-of-living/leisure',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'activity': activity,
        'price': price,
        'city': city,
        'admin': os.environ.get('ADMIN_KEY')
        }))
    return response

class TestLeisureResource:
    def test_leisure_post_leisure_location_exist(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response_data['activity'] == 'Monthly Gym Membership'
        assert post_response_data['price'] == 48
        assert post_response_data['location']['id'] == 1
        assert post_response_data['location']['country'] == 'Australia'
        assert post_response_data['location']['city'] == 'Perth'
        assert post_response.status_code == HttpStatus.created_201.value
        assert Leisure.query.count() == 1
    
    def test_leisure_post_leisure_location_exist_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        post_response = client.post('/v1/cost-of-living/leisure',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'activity': 'Monthly Gym Membership',
        'price': 48,
        'city': 'Perth'
        }))
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.forbidden_403.value
        assert post_response_data['message'] == 'Admin privileges needed'

    def test_leisure_post_leisure_location_notexist(self,client):
        response = create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Leisure.query.count() == 0

    def test_leisure_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        get_response = client.get('/v1/cost-of-living/leisure/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['activity'] == 'Monthly Gym Membership'
        assert get_response_data['price'] == 48
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_notexist_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        get_response = client.get('/v1/cost-of-living/leisure/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_leisure_get_country_city_abbreviation(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        create_leisure(client,'Monthly Gym Membership', 50, 'Melbourne')
        create_leisure(client,'Monthly Gym Membership', 61, 'Sydney')
        create_leisure(client,'Monthly Gym Membership', 93, 'Zurich')
        get_response = client.get('/v1/cost-of-living/leisure?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['activity'] == 'Monthly Gym Membership'
        assert get_response_data[0]['price'] == 69.6
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_country_city_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        create_leisure(client,'Monthly Gym Membership', 50, 'Melbourne')
        create_leisure(client,'Monthly Gym Membership', 61, 'Sydney')
        create_leisure(client,'Monthly Gym Membership', 93, 'Zurich')
        get_response = client.get('/v1/cost-of-living/leisure?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['activity'] == 'Monthly Gym Membership'
        assert get_response_data[0]['price'] == 48
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_country_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        create_leisure(client,'Monthly Gym Membership', 50, 'Melbourne')
        create_leisure(client,'Monthly Gym Membership', 61, 'Sydney')
        create_leisure(client,'Monthly Gym Membership', 93, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/leisure?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['leisure data']) == 3
        assert get_first_page_response_data['leisure data'][0]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][0]['price'] == 48
        assert get_first_page_response_data['leisure data'][0]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][1]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][1]['price'] == 50
        assert get_first_page_response_data['leisure data'][1]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['leisure data'][2]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][2]['price'] == 61
        assert get_first_page_response_data['leisure data'][2]['location']['id'] == 3
        assert get_first_page_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/leisure?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/leisure?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_country_abbreviation_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        create_leisure(client,'Monthly Gym Membership', 50, 'Melbourne')
        create_leisure(client,'Monthly Gym Membership', 61, 'Sydney')
        create_leisure(client,'Monthly Gym Membership', 93, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/leisure?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['leisure data']) == 3
        assert get_first_page_response_data['leisure data'][0]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][0]['price'] == 69.6
        assert get_first_page_response_data['leisure data'][0]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][1]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][1]['price'] == 72.5
        assert get_first_page_response_data['leisure data'][1]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['leisure data'][2]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][2]['price'] == 88.45
        assert get_first_page_response_data['leisure data'][2]['location']['id'] == 3
        assert get_first_page_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['count'] == 3
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/leisure?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/leisure?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_city_abbreviation_country_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        create_leisure(client,'Monthly Gym Membership', 50, 'Melbourne')
        create_leisure(client,'Monthly Gym Membership', 61, 'Sydney')
        create_leisure(client,'Monthly Gym Membership', 93, 'Zurich')
        get_response = client.get('/v1/cost-of-living/leisure?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['activity'] == 'Monthly Gym Membership'
        assert get_response_data[0]['price'] == 69.6
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_country_none_city_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        create_leisure(client,'Monthly Gym Membership', 50, 'Melbourne')
        create_leisure(client,'Monthly Gym Membership', 61, 'Sydney')
        create_leisure(client,'Monthly Gym Membership', 93, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/leisure',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['leisure data']) == 4
        assert get_first_page_response_data['leisure data'][0]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][0]['price'] == 48
        assert get_first_page_response_data['leisure data'][0]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][1]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][1]['price'] == 50
        assert get_first_page_response_data['leisure data'][1]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['leisure data'][2]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][2]['price'] == 61
        assert get_first_page_response_data['leisure data'][2]['location']['id'] == 3
        assert get_first_page_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['leisure data'][3]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][3]['price'] == 93
        assert get_first_page_response_data['leisure data'][3]['location']['id'] == 4
        assert get_first_page_response_data['leisure data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['leisure data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/leisure?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/leisure?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_city_country_none_abbreviation_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        create_leisure(client,'Monthly Gym Membership', 50, 'Melbourne')
        create_leisure(client,'Monthly Gym Membership', 61, 'Sydney')
        create_leisure(client,'Monthly Gym Membership', 93, 'Zurich')
        get_response = client.get('/v1/cost-of-living/leisure?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['activity'] == 'Monthly Gym Membership'
        assert get_response_data[0]['price'] == 48
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_abbreviation_country_none_city_none(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_currency(client,'CHF',0.92)
        create_location(client,'Australia','Perth','AUD')
        create_location(client,'Australia','Melbourne','AUD')
        create_location(client,'Australia','Sydney','AUD')
        create_location(client,'Switzerland','Zurich','CHF')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        create_leisure(client,'Monthly Gym Membership', 50, 'Melbourne')
        create_leisure(client,'Monthly Gym Membership', 61, 'Sydney')
        create_leisure(client,'Monthly Gym Membership', 93, 'Zurich')
        get_first_page_response = client.get('/v1/cost-of-living/leisure?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['leisure data']) == 4
        assert get_first_page_response_data['leisure data'][0]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][0]['price'] == 69.6
        assert get_first_page_response_data['leisure data'][0]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][1]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][1]['price'] == 72.5
        assert get_first_page_response_data['leisure data'][1]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][1]['location']['city'] == 'Melbourne'
        assert get_first_page_response_data['leisure data'][2]['activity'] == 'Monthly Gym Membership'
        assert get_first_page_response_data['leisure data'][2]['price'] == 88.45
        assert get_first_page_response_data['leisure data'][2]['location']['id'] == 3
        assert get_first_page_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][2]['location']['city'] == 'Sydney'
        assert get_first_page_response_data['leisure data'][3]['price'] == 134.85
        assert get_first_page_response_data['leisure data'][3]['location']['id'] == 4
        assert get_first_page_response_data['leisure data'][3]['location']['country'] == 'Switzerland'
        assert get_first_page_response_data['leisure data'][3]['location']['city'] == 'Zurich'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/cost-of-living/leisure?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['results']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/cost-of-living/leisure?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_leisure_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/leisure/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'activity': '1hr Tennis Court Rent',
            'price': 12.64,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/cost-of-living/leisure/1',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['activity'] == '1hr Tennis Court Rent'
        assert get_response_data['price'] == 12.64
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_update_no_id_exist(self,client):
        patch_response = client.patch('/v1/cost-of-living/leisure/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'activity': '1hr Tennis Court Rent',
            'price': 12.64,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.notfound_404.value
        assert Leisure.query.count() == 0
    
    def test_leisure_update_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        patch_response = client.patch('/v1/cost-of-living/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item': 'Mens Leather Business Shoes',
        'price': 194
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_leisure_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.no_content_204.value
        assert Leisure.query.count() == 0

    def test_leisure_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/cost-of-living/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Leisure.query.count() == 0
    
    def test_leisure_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        delete_response = client.delete('/v1/cost-of-living/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'