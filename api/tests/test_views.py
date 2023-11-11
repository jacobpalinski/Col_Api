import pytest
import time
import os
from flask import json, url_for
from httpstatus import HttpStatus
from models import (orm,User,UserSchema,BlacklistToken,Currency,CurrencySchema,Location,LocationSchema,
HomePurchase,HomePurchaseSchema,Rent,RentSchema,Utilities,UtilitiesSchema,
Transportation,TransportationSchema,FoodBeverage, FoodBeverageSchema,
Childcare,ChildcareSchema,Apparel, ApparelSchema, Leisure,LeisureSchema)
from datetime import datetime, date
from dotenv import load_dotenv
from unittest.mock import call
from fixtures import *

class TestUserResource:
    def test_user_post_no_user_no_admin(self,client):
        response = client.post('/v1/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email' : TEST_EMAIL,
            'password': TEST_PASSWORD
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Successfully registered'
        assert response.status_code == HttpStatus.created_201.value
        assert User.query.count() == 1
        assert User.query.first().admin == False
    
    def test_user_post_no_user_with_admin(self,client):
        response = client.post('/v1/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email' : TEST_EMAIL,
            'password': TEST_PASSWORD,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Successfully registered with admin privileges'
        assert response.status_code == HttpStatus.created_201.value
        assert User.query.count() == 1
        assert User.query.first().admin == True

    def test_user_post_exist_user(self,client):
        response = client.post('/v1/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
            }))
        second_post_response = client.post('/v1/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
            }))
        second_post_response_data = json.loads(second_post_response.get_data(as_text = True))
        assert second_post_response_data['message'] == 'User already exists. Please log in'
        assert second_post_response.status_code == HttpStatus.conflict_409.value
        assert User.query.count() == 1
    
    @pytest.mark.parametrize('invalid_email', ['testgmail.com', 'test@gmailcom'])
    def test_user_post_invalid_schema_email(self, client, invalid_email):
        response = client.post('/v1/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email': invalid_email,
            'password': TEST_PASSWORD
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Invalid email address'
        assert response.status_code == HttpStatus.bad_request_400.value
        assert User.query.count() == 0
    
    @pytest.mark.parametrize('invalid_password', ['Apple3$',
    'awdoawdawmdawmdkawdawk$3wwodpawdm', 'apple3$!', 'APPLE3$!', 'Apples$!',
    'Apple321'])
    def test_user_post_invalid_password(self, client, invalid_password):
        response = client.post('/v1/auth/user',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email': TEST_EMAIL,
            'password': invalid_password
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Invalid password'
        assert response.status_code == HttpStatus.unauthorized_401.value
        assert User.query.count() == 0
    
    def test_user_get_valid_token(self,client,create_user,login):
        get_response = client.get('/v1/auth/user',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        print(get_response_data)
        assert get_response_data['details']['user_id'] == 1
        assert get_response_data['details']['email'] == TEST_EMAIL
        assert datetime.strptime(get_response_data['details']['creation_date'],'%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d') == date.today().strftime('%Y-%m-%d')
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_user_get_no_token(self,client):
        get_response = client.get('/v1/auth/user',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer "})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['message'] == 'Provide a valid auth token'
        assert get_response.status_code == HttpStatus.forbidden_403.value

    def test_user_get_invalid_token(self,client):
        get_response = client.get('/v1/auth/user', headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer invalid token"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['message'] == 'Invalid token. Please log in again'
        assert get_response.status_code == HttpStatus.unauthorized_401.value

    def test_user_get_expired_token(self,client,create_user,login):
        time.sleep(6)
        get_response = client.get('/v1/auth/user',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['message'] == 'Signature expired. Please log in again'
        assert get_response.status_code == HttpStatus.unauthorized_401.value

    def test_user_get_malformed_bearer_token(self,client,create_user,login):
        get_response = client.get('/v1/auth/user',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer{login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['message'] == 'Bearer token malformed'
        assert get_response.status_code == HttpStatus.unauthorized_401.value

class TestLoginResource:
    def test_login_valid_user(self,client,create_user):
        response = client.post('/v1/auth/login',
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
        response = client.post('/v1/auth/login',
            headers = {'Content-Type' : 'application/json'},
            data = json.dumps({
            'email' : TEST_EMAIL,
            'password': TEST_PASSWORD
            }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'User does not exist'
        assert response.status_code == HttpStatus.notfound_404.value

class TestLogoutResource:
    def test_logout_valid_token(self,client,create_user,login):
        response = client.post('/v1/auth/logout', headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Successfully logged out'
        assert response.status_code == HttpStatus.ok_200.value
        assert BlacklistToken.query.count() == 1

    def test_logout_no_token(self,client):
        response = client.post('/v1/auth/logout',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer "})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Provide a valid auth token'
        assert response.status_code == HttpStatus.forbidden_403.value
        assert BlacklistToken.query.count() == 0

    def test_logout_invalid_token(self,client):
        response = client.post('/v1/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer invalid token"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Provide a valid auth token'
        assert response.status_code == HttpStatus.forbidden_403.value
        assert BlacklistToken.query.count() == 0

    def test_logout_expired_token(self,client,create_user,login):
        time.sleep(6)
        response = client.post('/v1/auth/logout', headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Signature expired. Please log in again'
        assert response.status_code == HttpStatus.unauthorized_401.value

    def test_logout_blacklisted_token(self,client,create_user,login):
        blacklist_token = BlacklistToken(token = login['auth_token'])
        blacklist_token.add(blacklist_token)
        assert BlacklistToken.query.count() == 1
        response = client.post('/v1/auth/logout', headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Provide a valid auth token'
        assert response.status_code == HttpStatus.forbidden_403.value
        assert BlacklistToken.query.count() == 1

    def test_logout_malformed_token(self,client,create_user,login):
        response = client.post('/v1/auth/logout', headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer{login['auth_token']}"})
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Bearer token malformed'
        assert response.status_code == HttpStatus.unauthorized_401.value
        assert BlacklistToken.query.count() == 0

class TestResetPasswordResource:
    def test_reset_password_exist_user(self,client,create_user):
        response = client.post('/v1/auth/user/password_reset',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD
        }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Password reset successful'
        assert response.status_code == HttpStatus.ok_200.value

    def test_reset_password_no_user(self,client):
        response = client.post('/v1/auth/user/password_reset',
        headers = {'Content-Type' : 'application/json'},
        data = json.dumps({
        'email' : TEST_EMAIL,
        'password': TEST_PASSWORD
        }))
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'User does not exist'
        assert response.status_code == HttpStatus.unauthorized_401.value

class TestCurrencyResource:
    def test_currency_get_with_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        get_response = client.get('/v1/currencies/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['abbreviation'] == 'AUD'
        assert get_response_data['usd_to_local_exchange_rate'] == 1.55
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_currency_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        get_response = client.get('/v1/currencies/5',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_currency_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        delete_response = client.delete('/v1/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Currency id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Currency.query.count() == 3

    def test_currency_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Currency.query.count() == 0
    
    def test_currency_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        delete_response = client.delete('/v1/currencies/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestCurrencyListResource:
    def test_currency_post_currency_no_admin(self, client, mock_boto3_s3, mock_environment_variables, current_date):
        response = client.post('/v1/currencies',
        headers = {'Content-Type': 'application/json'})
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.bad_request_400.value
        assert response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
        assert Currency.query.count() == 0

    def test_currency_post_currency_incorrect_admin(self, client, mock_boto3_s3, mock_environment_variables, current_date):
        response = client.post('/v1/currencies',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert Currency.query.count() == 0
    
    def test_currency_post_currency_with_admin(self, client, mock_boto3_s3, mock_environment_variables, current_date):
        response = create_currency(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        mock_boto3_s3.get_object.assert_called_once_with(Bucket = 'test-bucket-transformed', Key = f'locations_with_currencies{current_date}')
        assert response.status_code == HttpStatus.created_201.value
        assert response_data['message'] == 'Successfully added 4 currencies'
        assert Currency.query.count() == 4

    def test_currency_post_currency_already_exists(self, client, mock_boto3_s3, mock_environment_variables, current_date):
        expected_get_object_calls = [call(Bucket = 'test-bucket-transformed', Key = f'locations_with_currencies{current_date}'),
        call(Bucket = 'test-bucket-transformed', Key = f'locations_with_currencies{current_date}')]
        response = create_currency(client, mock_environment_variables)
        second_response = create_currency(client, mock_environment_variables)
        response_data = json.loads(second_response.get_data(as_text = True))
        assert mock_boto3_s3.get_object.call_count == 2
        assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
        assert second_response.status_code == HttpStatus.created_201.value
        assert response_data['message'] == 'Successfully added 0 currencies'
        assert Currency.query.count() == 4
    
    def test_currency_patch_updated_data(self, client, create_user, login, mock_boto3_s3, mock_boto3_s3_patch_modified, mock_environment_variables, current_date):
        create_currency(client, mock_environment_variables)
        patch_response = currency_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'usd_to_local_exchange_rate was successfully updated for 1 currencies'
        get_response = client.get('/v1/currencies',
        headers = {'Content-Type': 'application/json',
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response.status_code == HttpStatus.ok_200.value
        assert len(get_response_data['currencies']) == 4
        assert get_response_data['currencies'][0]['abbreviation'] == 'AUD'
        assert get_response_data['currencies'][0]['usd_to_local_exchange_rate'] == 1.54
        assert get_response_data['currencies'][1]['abbreviation'] == 'HKD'
        assert get_response_data['currencies'][1]['usd_to_local_exchange_rate'] == 7.82
        assert get_response_data['currencies'][2]['abbreviation'] == 'NZD'
        assert get_response_data['currencies'][2]['usd_to_local_exchange_rate'] == 1.69
        assert get_response_data['currencies'][3]['abbreviation'] == 'PYG'
        assert get_response_data['currencies'][3]['usd_to_local_exchange_rate'] == 7258.93
    
    def test_currency_patch_no_updated_data(self, client, create_user, login, mock_boto3_s3, mock_environment_variables, current_date):
        create_currency(client, mock_environment_variables)
        patch_response = client.patch('/v1/currencies',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'admin': os.environ.get('ADMIN_KEY')
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'usd_to_local_exchange_rate was successfully updated for 0 currencies'
        get_response = client.get('/v1/currencies',
        headers = {'Content-Type': 'application/json',
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response.status_code == HttpStatus.ok_200.value
        assert len(get_response_data['currencies']) == 4
        assert get_response_data['currencies'][0]['abbreviation'] == 'AUD'
        assert get_response_data['currencies'][0]['usd_to_local_exchange_rate'] == 1.55
        assert get_response_data['currencies'][1]['abbreviation'] == 'HKD'
        assert get_response_data['currencies'][1]['usd_to_local_exchange_rate'] == 7.82
        assert get_response_data['currencies'][2]['abbreviation'] == 'NZD'
        assert get_response_data['currencies'][2]['usd_to_local_exchange_rate'] == 1.69
        assert get_response_data['currencies'][3]['abbreviation'] == 'PYG'
        assert get_response_data['currencies'][3]['usd_to_local_exchange_rate'] == 7258.93
    
    def test_currency_patch_no_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        patch_response = client.patch('/v1/currencies',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_currency_patch_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        response = client.patch('/v1/currencies',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'
    
    def test_currency_get_without_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/currencies',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['currencies']) == 4
        assert get_first_page_response_data['currencies'][0]['abbreviation'] == 'AUD'
        assert get_first_page_response_data['currencies'][0]['usd_to_local_exchange_rate'] == 1.55
        assert get_first_page_response_data['currencies'][1]['abbreviation'] == 'HKD'
        assert get_first_page_response_data['currencies'][1]['usd_to_local_exchange_rate'] == 7.82
        assert get_first_page_response_data['currencies'][2]['abbreviation'] == 'NZD'
        assert get_first_page_response_data['currencies'][2]['usd_to_local_exchange_rate'] == 1.69
        assert get_first_page_response_data['currencies'][3]['abbreviation'] == 'PYG'
        assert get_first_page_response_data['currencies'][3]['usd_to_local_exchange_rate'] == 7258.93
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/currencies?page=2',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/currencies?page=1'
        assert get_second_page_response_data['next'] == None
        assert len(get_second_page_response_data['currencies']) == 0
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestLocationResource:
    def test_location_get_with_id(self,client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        get_response = client.get('/v1/locations/1',
        headers = {"Content-Type": "application/json",
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['country'] == 'Australia'
        assert get_response_data['city'] == 'Perth'
        assert get_response_data['currency']['id'] == 1
        assert get_response_data['currency']['abbreviation'] == 'AUD'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_location_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        get_response = client.get('/v1/locations/5',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value
    
    def test_location_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        delete_response = client.delete('/v1/locations/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Location id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Location.query.count() == 3

    def test_location_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/locations/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Location.query.count() == 0
    
    def test_location_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        delete_response = client.delete('/v1/locations/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestLocationListResource:
    def test_location_post_location_currency_notexist(self, client, mock_environment_variables, mock_boto3_s3):
        response = create_location(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified currency doesnt exist in /currencies/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Location.query.count() == 0

    def test_location_post_location_no_admin(self, client, mock_boto3_s3, mock_environment_variables, current_date):
        response = client.post('/v1/locations',
        headers = {'Content-Type': 'application/json'})
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.bad_request_400.value
        assert response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
        assert Location.query.count() == 0
    
    def test_location_post_location_incorrect_admin(self, client, mock_boto3_s3, mock_environment_variables, current_date):
        response = client.post('/v1/locations',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert Location.query.count() == 0

    def test_location_post_location_with_admin(self,client, create_user, login, mock_boto3_s3, mock_environment_variables, current_date):
        create_currency(client, mock_environment_variables)
        post_response = create_location(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == 'Successfully added 4 locations'
        assert Location.query.count() == 4
    
    def test_location_post_location_already_exists(self, client, mock_boto3_s3, mock_environment_variables, current_date):
        create_currency(client, mock_environment_variables)
        expected_get_object_calls = [call(Bucket = 'test-bucket-transformed', Key = f'locations_with_currencies{current_date}'),
        call(Bucket = 'test-bucket-transformed', Key = f'locations_with_currencies{current_date}'),
        call(Bucket = 'test-bucket-transformed', Key = f'locations_with_currencies{current_date}')]
        response = create_location(client, mock_environment_variables)
        second_response = create_location(client, mock_environment_variables)
        response_data = json.loads(second_response.get_data(as_text = True))
        assert mock_boto3_s3.get_object.call_count == 3
        assert mock_boto3_s3.get_object.call_args_list == expected_get_object_calls
        assert second_response.status_code == HttpStatus.created_201.value
        assert response_data['message'] == 'Successfully added 0 locations'
        assert Location.query.count() == 4

    def test_location_get_without_id(self, client, create_user, login, mock_boto3_s3, mock_environment_variables, current_date):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/locations',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['locations']) == 4
        assert get_first_page_response_data['locations'][0]['country'] == 'Australia'
        assert get_first_page_response_data['locations'][0]['city'] == 'Perth'
        assert get_first_page_response_data['locations'][0]['currency']['id'] == 1
        assert get_first_page_response_data['locations'][0]['currency']['abbreviation'] == 'AUD'
        assert get_first_page_response_data['locations'][1]['country'] == 'Hong Kong'
        assert get_first_page_response_data['locations'][1]['city'] == 'Hong Kong'
        assert get_first_page_response_data['locations'][1]['currency']['id'] == 2
        assert get_first_page_response_data['locations'][1]['currency']['abbreviation'] == 'HKD'
        assert get_first_page_response_data['locations'][2]['country'] == 'New Zealand'
        assert get_first_page_response_data['locations'][2]['city'] == 'Auckland'
        assert get_first_page_response_data['locations'][2]['currency']['id'] == 3
        assert get_first_page_response_data['locations'][2]['currency']['abbreviation'] == 'NZD'
        assert get_first_page_response_data['locations'][3]['country'] == 'Paraguay'
        assert get_first_page_response_data['locations'][3]['city'] == 'Asuncion'
        assert get_first_page_response_data['locations'][3]['currency']['id'] == 4
        assert get_first_page_response_data['locations'][3]['currency']['abbreviation'] == 'PYG'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/locations?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['locations']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/locations?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestHomePurchaseResource:
    def test_homepurchase_get_with_id(self, client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_response = client.get('/v1/homepurchase/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['property_location'] == 'City Centre'
        assert get_response_data['price_per_sqm'] == 30603.04
        assert get_response_data['mortgage_interest'] == 3.22
        assert get_response_data['location']['id'] == 2
        assert get_response_data['location']['country'] == 'Hong Kong'
        assert get_response_data['location']['city'] == 'Hong Kong'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_homepurchase_get_notexist_id(self, client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_response = client.get('/v1/homepurchase/5',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_homepurchase_delete(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        delete_response = client.delete('/v1/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'HomePurchase id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert HomePurchase.query.count() == 3

    def test_homepurchase_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert HomePurchase.query.count() == 0
    
    def test_homepurchase_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        delete_response = client.delete('/v1/homepurchase/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestHomePurchaseListResource:
    def test_homepurchase_post_homepurchase_location_notexist(self, client, mock_environment_variables, mock_boto3_s3):
        response = create_homepurchase(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert HomePurchase.query.count() == 0
    
    def test_homepurchase_post_homepurchase_no_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/homepurchase',
        headers = {'Content-Type': 'application/json'})
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.bad_request_400.value
        assert response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
        assert HomePurchase.query.count() == 0
    
    def test_homepurchase_post_homepurchase_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/homepurchase',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert HomePurchase.query.count() == 0

    def test_homepurchase_post_homepurchase_with_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = create_homepurchase(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == f'Successfully added 4 homepurchase records'
        assert HomePurchase.query.count() == 4
    
    def test_homepurchase_patch_updated_data(self, client, create_user, login, mock_boto3_s3, mock_boto3_s3_patch_modified, mock_environment_variables, current_date):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        patch_response = homepurchase_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 2 homepurchase records'
        get_response = client.get('/v1/homepurchase',
        headers = {'Content-Type': 'application/json',
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response.status_code == HttpStatus.ok_200.value
        assert len(get_response_data['home purchase data']) == 4
        assert get_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_response_data['home purchase data'][0]['price_per_sqm'] == 30603.04
        assert get_response_data['home purchase data'][0]['mortgage_interest'] == 3.22
        assert get_response_data['home purchase data'][0]['location']['id'] == 2
        assert get_response_data['home purchase data'][0]['location']['country'] == 'Hong Kong'
        assert get_response_data['home purchase data'][0]['location']['city'] == 'Hong Kong'
        assert get_response_data['home purchase data'][1]['property_location'] == 'Outside of Centre'
        assert get_response_data['home purchase data'][1]['price_per_sqm'] == 20253.04
        assert get_response_data['home purchase data'][1]['mortgage_interest'] == 3.22
        assert get_response_data['home purchase data'][1]['location']['id'] == 2
        assert get_response_data['home purchase data'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['home purchase data'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['home purchase data'][2]['property_location'] == 'Outside of Centre'
        assert get_response_data['home purchase data'][2]['price_per_sqm'] == 7120.84
        assert get_response_data['home purchase data'][2]['mortgage_interest'] == 5.99
        assert get_response_data['home purchase data'][2]['location']['id'] == 1
        assert get_response_data['home purchase data'][2]['location']['country'] == 'Perth'
        assert get_response_data['home purchase data'][2]['location']['city'] == 'Australia'
        assert get_response_data['home purchase data'][3]['property_location'] == 'Outside of Centre'
        assert get_response_data['home purchase data'][3]['price_per_sqm'] == 5824.95
        assert get_response_data['home purchase data'][3]['mortgage_interest'] == 5.99
        assert get_response_data['home purchase data'][3]['location']['id'] == 1
        assert get_response_data['home purchase data'][3]['location']['country'] == 'Perth'
        assert get_response_data['home purchase data'][3]['location']['city'] == 'Australia'
    
    def test_homepurchase_patch_no_updated_data(self, client, create_user, login, mock_boto3_s3, mock_environment_variables, current_date):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        patch_response = homepurchase_patch_updated_data(client, mock_environment_variables, mock_boto3_s3)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 0 homepurchase records'
        get_response = client.get('/v1/homepurchase',
        headers = {'Content-Type': 'application/json',
        "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response.status_code == HttpStatus.ok_200.value
        assert len(get_response_data['home purchase data']) == 4
        assert get_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_response_data['home purchase data'][0]['price_per_sqm'] == 6741.52
        assert get_response_data['home purchase data'][0]['mortgage_interest'] == 5.99
        assert get_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_response_data['home purchase data'][1]['property_location'] == 'City Centre'
        assert get_response_data['home purchase data'][1]['price_per_sqm'] == 30603.04
        assert get_response_data['home purchase data'][1]['mortgage_interest'] == 3.22
        assert get_response_data['home purchase data'][1]['location']['id'] == 2
        assert get_response_data['home purchase data'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['home purchase data'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['home purchase data'][2]['property_location'] == 'Outside of Centre'
        assert get_response_data['home purchase data'][2]['price_per_sqm'] == 5395.77
        assert get_response_data['home purchase data'][2]['mortgage_interest'] == 5.99
        assert get_response_data['home purchase data'][2]['location']['id'] == 1
        assert get_response_data['home purchase data'][2]['location']['country'] == 'Australia'
        assert get_response_data['home purchase data'][2]['location']['city'] == 'Perth'
        assert get_response_data['home purchase data'][3]['property_location'] == 'Outside of Centre'
        assert get_response_data['home purchase data'][3]['price_per_sqm'] == 20253.04
        assert get_response_data['home purchase data'][3]['mortgage_interest'] == 3.22
        assert get_response_data['home purchase data'][3]['location']['id'] == 2
        assert get_response_data['home purchase data'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['home purchase data'][3]['location']['city'] == 'Hong Kong'
    
    def test_homepurchase_patch_no_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        patch_response = client.patch('/v1/homepurchase',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_homepurchase_patch_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        response = client.patch('/v1/homepurchase',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_homepurchase_get_country_city_abbreviation(self,client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_response = client.get('/v1/homepurchase?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['price_per_sqm'] == 10449.36
        assert get_response_data[0]['mortgage_interest'] == 5.99
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['property_location'] == 'Outside of Centre'
        assert get_response_data[1]['price_per_sqm'] == 8363.44
        assert get_response_data[1]['mortgage_interest'] == 5.99
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_homepurchase_get_country_city_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_response = client.get('/v1/homepurchase?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['price_per_sqm'] == 6741.52
        assert get_response_data[0]['mortgage_interest'] == 5.99
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['property_location'] == 'Outside of Centre'
        assert get_response_data[1]['price_per_sqm'] == 5395.77
        assert get_response_data[1]['mortgage_interest'] == 5.99
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_homepurchase_get_country_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/homepurchase?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['home purchase data']) == 2
        assert get_first_page_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][0]['price_per_sqm'] == 6741.52
        assert get_first_page_response_data['home purchase data'][0]['mortgage_interest'] == 5.99
        assert get_first_page_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][1]['property_location'] == 'Outside of Centre'
        assert get_first_page_response_data['home purchase data'][1]['price_per_sqm'] == 5395.77
        assert get_first_page_response_data['home purchase data'][1]['mortgage_interest'] == 5.99
        assert get_first_page_response_data['home purchase data'][1]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 2
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/homepurchase?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['home purchase data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/homepurchase?country=Australia&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_homepurchase_get_country_abbreviation_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/homepurchase?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['home purchase data']) == 2
        assert get_first_page_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][0]['price_per_sqm'] == 10449.36
        assert get_first_page_response_data['home purchase data'][0]['mortgage_interest'] == 5.99
        assert get_first_page_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][1]['property_location'] == 'Outside of Centre'
        assert get_first_page_response_data['home purchase data'][1]['price_per_sqm'] == 8363.44
        assert get_first_page_response_data['home purchase data'][1]['mortgage_interest'] == 5.99
        assert get_first_page_response_data['home purchase data'][1]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 2
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/homepurchase?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['home purchase data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/homepurchase?country=Australia&abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_homepurchase_get_city_abbreviation_country_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_response = client.get('/v1/homepurchase?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['price_per_sqm'] == 10449.36
        assert get_response_data[0]['mortgage_interest'] == 5.99
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['property_location'] == 'Outside of Centre'
        assert get_response_data[1]['price_per_sqm'] == 8363.44
        assert get_response_data[1]['mortgage_interest'] == 5.99
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_homepurchase_get_country_none_city_none_abbreviation_none(self,client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/homepurchase',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['home purchase data']) == 4
        assert get_first_page_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][0]['price_per_sqm'] == 6741.52
        assert get_first_page_response_data['home purchase data'][0]['mortgage_interest'] == 5.99
        assert get_first_page_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][1]['price_per_sqm'] == 30603.04
        assert get_first_page_response_data['home purchase data'][1]['mortgage_interest'] == 3.22
        assert get_first_page_response_data['home purchase data'][1]['location']['id'] == 2
        assert get_first_page_response_data['home purchase data'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['home purchase data'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['home purchase data'][2]['property_location'] == 'Outside of Centre'
        assert get_first_page_response_data['home purchase data'][2]['price_per_sqm'] == 5395.77
        assert get_first_page_response_data['home purchase data'][2]['mortgage_interest'] == 5.99
        assert get_first_page_response_data['home purchase data'][2]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][3]['property_location'] == 'Outside of Centre'
        assert get_first_page_response_data['home purchase data'][3]['price_per_sqm'] == 20253.04
        assert get_first_page_response_data['home purchase data'][3]['mortgage_interest'] == 3.22
        assert get_first_page_response_data['home purchase data'][3]['location']['id'] == 2
        assert get_first_page_response_data['home purchase data'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['home purchase data'][3]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/homepurchase?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['home purchase data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/homepurchase?page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

    def test_homepurchase_get_city_country_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_response = client.get('/v1/homepurchase?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['price_per_sqm'] == 6741.52
        assert get_response_data[0]['mortgage_interest'] == 5.99
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['property_location'] == 'Outside of Centre'
        assert get_response_data[1]['price_per_sqm'] == 5395.77
        assert get_response_data[1]['mortgage_interest'] == 5.99
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_homepurchase_get_abbreviation_country_none_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_homepurchase(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/homepurchase?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['home purchase data']) == 4
        assert get_first_page_response_data['home purchase data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][0]['price_per_sqm'] == 10449.36
        assert get_first_page_response_data['home purchase data'][0]['mortgage_interest'] == 5.99
        assert get_first_page_response_data['home purchase data'][0]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['home purchase data'][1]['price_per_sqm'] == 47434.71
        assert get_first_page_response_data['home purchase data'][1]['mortgage_interest'] == 3.22
        assert get_first_page_response_data['home purchase data'][1]['location']['id'] == 2
        assert get_first_page_response_data['home purchase data'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['home purchase data'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['home purchase data'][2]['property_location'] == 'Outside of Centre'
        assert get_first_page_response_data['home purchase data'][2]['price_per_sqm'] == 8363.44
        assert get_first_page_response_data['home purchase data'][2]['mortgage_interest'] == 5.99
        assert get_first_page_response_data['home purchase data'][2]['location']['id'] == 1
        assert get_first_page_response_data['home purchase data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['home purchase data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['home purchase data'][3]['property_location'] == 'Outside of Centre'
        assert get_first_page_response_data['home purchase data'][3]['price_per_sqm'] == 31392.21
        assert get_first_page_response_data['home purchase data'][3]['mortgage_interest'] == 3.22
        assert get_first_page_response_data['home purchase data'][3]['location']['id'] == 2
        assert get_first_page_response_data['home purchase data'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['home purchase data'][3]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['count'] == 4
        assert get_first_page_response_data['previous'] == None
        assert get_first_page_response_data['next'] == None
        assert get_first_page_response.status_code == HttpStatus.ok_200.value
        get_second_page_response = client.get('/v1/homepurchase?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['home purchase data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/homepurchase?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestRentResource:
    def test_rent_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        get_response = client.get('/v1/rent/1',
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
        get_response = client.get('/v1/rent/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_rent_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642.43, 'Perth')
        delete_response = client.delete('/v1/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Rent id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Rent.query.count() == 0

    def test_rent_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Rent.query.count() == 0
    
    def test_rent_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642.43, 'Perth')
        delete_response = client.delete('/v1/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestRentListResource:
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
        post_response = client.post('/v1/rent',
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
    
    def test_rent_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_rent(client,'City Centre', 1, 1642, 'Perth')
        patch_response = client.patch('/v1/rent/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'property_location': 'Outside City Centre',
            'bedrooms': 3,
            'monthly_price': 2526,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/rent/1',
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
        patch_response = client.patch('/v1/rent/1',
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
        patch_response = client.patch('/v1/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'price_per_sqm': 7000,
        'mortgage_interest': 6.01
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

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
        get_response = client.get('/v1/rent?country=Australia&city=Perth&abbreviation=AUD',
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
        get_response = client.get('/v1/rent?country=Australia&city=Perth',
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
        get_first_page_response = client.get('/v1/rent?country=Australia',
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
        get_second_page_response = client.get('/v1/rent?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['rental data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/rent?country=Australia&page=1'
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
        get_first_page_response = client.get('/v1/rent?country=Australia&abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/rent?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['rental data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/rent?country=Australia&abbreviation=AUD&page=1'
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
        get_response = client.get('/v1/rent?city=Perth&abbreviation=AUD',
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
        get_first_page_response = client.get('/v1/rent',
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
        get_second_page_response = client.get('/v1/rent?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['rental data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/rent?page=1'
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
        get_response = client.get('/v1/rent?city=Perth',
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
        get_first_page_response = client.get('/v1/rent?abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/rent?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['rental data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/rent?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestUtilitiesResource:
    def test_utilities_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        get_response = client.get('/v1/utilities/1',
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
        get_response = client.get('/v1/utilities/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value
    
    def test_utilities_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        patch_response = client.patch('/v1/utilities/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'utility': 'Internet',
            'monthly_price': 55,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/utilities/1',
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
        patch_response = client.patch('/v1/utilities/1',
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
        patch_response = client.patch('/v1/utilities/1',
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
        delete_response = client.delete('/v1/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Utilities id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Utilities.query.count() == 0

    def test_utilities_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Utilities.query.count() == 0
    
    def test_utilities_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        delete_response = client.delete('/v1/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestUtilitiesListResource:
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
        post_response = client.post('/v1/utilities',
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
    
    def test_utilities_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_utilities(client,'Electricity, Heating, Cooling, Water and Garbage', 210, 'Perth')
        patch_response = client.patch('/v1/utilities/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'utility': 'Internet',
            'monthly_price': 55,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/utilities/1',
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
        patch_response = client.patch('/v1/utilities/1',
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
        patch_response = client.patch('/v1/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'property_location': 'Outside City Centre',
        'price_per_sqm': 7000,
        'mortgage_interest': 6.01
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

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
        get_response = client.get('/v1/utilities?country=Australia&city=Perth&abbreviation=AUD',
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
        get_response = client.get('/v1/utilities?country=Australia&city=Perth',
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
        get_first_page_response = client.get('/v1/utilities?country=Australia',
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
        get_second_page_response = client.get('/v1/utilities?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['utilities']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/utilities?country=Australia&page=1'
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
        get_first_page_response = client.get('/v1/utilities?country=Australia&abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/utilities?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['utilities']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/utilities?country=Australia&abbreviation=AUD&page=1'
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
        get_response = client.get('/v1/utilities?city=Perth&abbreviation=AUD',
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
        get_first_page_response = client.get('/v1/utilities',
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
        get_second_page_response = client.get('/v1/utilities?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['utilities']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/utilities?page=1'
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
        get_response = client.get('/v1/utilities?city=Perth',
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
        get_first_page_response = client.get('/v1/utilities?abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/utilities?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['utilities']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/utilities?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestTransportationResource:
    def test_transportation_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        get_response = client.get('/v1/transportation/1',
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
        get_response = client.get('/v1/transportation/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_transportation_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        delete_response = client.delete('/v1/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Transportation id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Transportation.query.count() == 0

    def test_transportation_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Transportation.query.count() == 0
    
    def test_transportation_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        delete_response = client.delete('/v1/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestTransportationListResource:
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
        post_response = client.post('/v1/transportation',
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
    
    def test_transportation_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_transportation(client,'Monthly Public Transportation Pass', 103, 'Perth')
        patch_response = client.patch('/v1/transportation/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'type': 'One-Way Ticket',
            'price': 2.76,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/transportation/1',
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
        patch_response = client.patch('/v1/transportation/1',
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
        patch_response = client.patch('/v1/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'type': 'One-Way Ticket',
        'price': 2.76,
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

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
        get_response = client.get('/v1/transportation?country=Australia&city=Perth&abbreviation=AUD',
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
        get_response = client.get('/v1/transportation?country=Australia&city=Perth',
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
        get_first_page_response = client.get('/v1/transportation?country=Australia',
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
        get_second_page_response = client.get('/v1/transportation?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['transportation data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/transportation?country=Australia&page=1'
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
        get_first_page_response = client.get('/v1/transportation?country=Australia&abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/transportation?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['transportation data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/transportation?country=Australia&abbreviation=AUD&page=1'
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
        get_response = client.get('/v1/transportation?city=Perth&abbreviation=AUD',
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
        get_first_page_response = client.get('/v1/transportation',
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
        get_second_page_response = client.get('/v1/transportation?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['transportation data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/transportation?page=1'
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
        get_response = client.get('/v1/transportation?city=Perth',
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
        get_first_page_response = client.get('/v1/transportation?abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/transportation?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['transportation data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/transportation?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestFoodBeverageResource:
    def test_foodbeverage_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        get_response = client.get('/v1/foodbeverage/1',
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
        get_response = client.get('/v1/foodbeverage/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_foodbeverage_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        delete_response = client.delete('/v1/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'FoodBeverage id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert FoodBeverage.query.count() == 0

    def test_foodbeverage_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert FoodBeverage.query.count() == 0
    
    def test_foodbeverage_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        delete_response = client.delete('/v1/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'
    
class TestFoodBeverageListResource:
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
        post_response = client.post('/v1/foodbeverage',
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
    
    def test_foodbeverage_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_foodbeverage(client,'Beverage', 'Supermarket', 'Milk 1L', 1.77, 'Perth')
        patch_response = client.patch('/v1/foodbeverage/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'item_category': 'Food',
            'purchase_point': 'Restaurant',
            'item': 'McMeal',
            'price': 10.24,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/foodbeverage/1',
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
        patch_response = client.patch('/v1/foodbeverage/1',
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
        patch_response = client.patch('/v1/foodbeverage/1',
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
        get_response = client.get('/v1/foodbeverage?country=Australia&city=Perth&abbreviation=AUD',
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
        get_response = client.get('/v1/foodbeverage?country=Australia&city=Perth',
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
        get_first_page_response = client.get('/v1/foodbeverage?country=Australia',
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
        get_second_page_response = client.get('/v1/foodbeverage?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['food and beverage data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/foodbeverage?country=Australia&page=1'
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
        get_first_page_response = client.get('/v1/foodbeverage?country=Australia&abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/foodbeverage?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['food and beverage data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/foodbeverage?country=Australia&abbreviation=AUD&page=1'
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
        get_response = client.get('/v1/foodbeverage?city=Perth&abbreviation=AUD',
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
        get_first_page_response = client.get('/v1/foodbeverage',
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
        get_second_page_response = client.get('/v1/foodbeverage?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['food and beverage data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/foodbeverage?page=1'
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
        get_response = client.get('/v1/foodbeverage?city=Perth',
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
        get_first_page_response = client.get('/v1/foodbeverage?abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/foodbeverage?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['food and beverage data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/foodbeverage?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestChildcareResource:
    def test_childcare_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        get_response = client.get('/v1/childcare/1',
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
        get_response = client.get('/v1/childcare/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value
    
    def test_childcare_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        patch_response = client.patch('/v1/childcare/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'type': 'International Primary School',
            'annual_price': 15547.56,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/childcare/1',
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
        patch_response = client.patch('/v1/childcare/1',
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
        patch_response = client.patch('/v1/childcare/1',
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
        delete_response = client.delete('/v1/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Childcare id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Childcare.query.count() == 0

    def test_childcare_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Childcare.query.count() == 0
    
    def test_childcare_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        delete_response = client.delete('/v1/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestChildcareListResource:
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
        post_response = client.post('/v1/childcare',
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
    
    def test_childcare_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_childcare(client,'Preschool', 19632, 'Perth')
        patch_response = client.patch('/v1/childcare/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'type': 'International Primary School',
            'annual_price': 15547.56,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/childcare/1',
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
        patch_response = client.patch('/v1/childcare/1',
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
        patch_response = client.patch('/v1/childcare/1',
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
        get_response = client.get('/v1/childcare?country=Australia&city=Perth&abbreviation=AUD',
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
        get_response = client.get('/v1/childcare?country=Australia&city=Perth',
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
        get_first_page_response = client.get('/v1/childcare?country=Australia',
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
        get_second_page_response = client.get('/v1/childcare?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['childcare data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/childcare?country=Australia&page=1'
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
        get_first_page_response = client.get('/v1/childcare?country=Australia&abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/childcare?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['childcare data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/childcare?country=Australia&abbreviation=AUD&page=1'
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
        get_response = client.get('/v1/childcare?city=Perth&abbreviation=AUD',
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
        get_first_page_response = client.get('/v1/childcare',
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
        get_second_page_response = client.get('/v1/childcare?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['childcare data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/childcare?page=1'
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
        get_response = client.get('/v1/childcare?city=Perth',
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
        get_first_page_response = client.get('/v1/childcare?abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/childcare?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['childcare data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/childcare?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestApparelResource:
    def test_apparel_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        get_response = client.get('/v1/apparel/1',
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
        get_response = client.get('/v1/apparel/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_apparel_delete(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        delete_response = client.delete('/v1/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Apparel id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Apparel.query.count() == 0

    def test_apparel_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Apparel.query.count() == 0
    
    def test_apparel_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        delete_response = client.delete('/v1/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestApparelListResource:
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
        post_response = client.post('/v1/apparel',
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
    
    def test_apparel_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_apparel(client,'Levis Pair of Jeans', 77, 'Perth')
        patch_response = client.patch('/v1/apparel/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'item': 'Mens Leather Business Shoes',
            'price': 194,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/apparel/1',
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
        patch_response = client.patch('/v1/apparel/1',
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
        patch_response = client.patch('/v1/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item': 'Mens Leather Business Shoes',
        'price': 194
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

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
        get_response = client.get('/v1/apparel?country=Australia&city=Perth&abbreviation=AUD',
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
        get_response = client.get('/v1/apparel?country=Australia&city=Perth',
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
        get_first_page_response = client.get('/v1/apparel?country=Australia',
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
        get_second_page_response = client.get('/v1/apparel?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['apparel data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/apparel?country=Australia&page=1'
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
        get_first_page_response = client.get('/v1/apparel?country=Australia&abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/apparel?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['apparel data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/apparel?country=Australia&abbreviation=AUD&page=1'
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
        get_response = client.get('/v1/apparel?city=Perth&abbreviation=AUD',
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
        get_first_page_response = client.get('/v1/apparel',
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
        get_second_page_response = client.get('/v1/apparel?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['apparel data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/apparel?page=1'
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
        get_response = client.get('/v1/apparel?city=Perth',
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
        get_first_page_response = client.get('/v1/apparel?abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/apparel?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['apparel data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/apparel?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value

class TestLesiureResource:
    def test_leisure_get_with_id(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        get_response = client.get('/v1/leisure/1',
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
        get_response = client.get('/v1/leisure/2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value
    
    def test_leisure_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        patch_response = client.patch('/v1/leisure/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'activity': '1hr Tennis Court Rent',
            'price': 12.64,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/leisure/1',
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
        patch_response = client.patch('/v1/leisure/1',
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
        patch_response = client.patch('/v1/leisure/1',
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
        delete_response = client.delete('/v1/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Leisure id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Leisure.query.count() == 0

    def test_leisure_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Leisure.query.count() == 0
    
    def test_leisure_delete_no_admin(self,client):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        delete_response = client.delete('/v1/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestLeisureListResource:
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
        post_response = client.post('/v1/leisure',
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
    
    def test_leisure_update(self,client,create_user,login):
        create_currency(client,'AUD',1.45)
        create_location(client,'Australia','Perth','AUD')
        create_leisure(client,'Monthly Gym Membership', 48, 'Perth')
        patch_response = client.patch('/v1/leisure/1',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'activity': '1hr Tennis Court Rent',
            'price': 12.64,
            'admin': os.environ.get('ADMIN_KEY')
            }))
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/leisure/1',
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
        patch_response = client.patch('/v1/leisure/1',
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
        patch_response = client.patch('/v1/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({
        'item': 'Mens Leather Business Shoes',
        'price': 194
        }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

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
        get_response = client.get('/v1/leisure?country=Australia&city=Perth&abbreviation=AUD',
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
        get_response = client.get('/v1/leisure?country=Australia&city=Perth',
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
        get_first_page_response = client.get('/v1/leisure?country=Australia',
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
        get_second_page_response = client.get('/v1/leisure?country=Australia&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['leisure data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/leisure?country=Australia&page=1'
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
        get_first_page_response = client.get('/v1/leisure?country=Australia&abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/leisure?country=Australia&abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['leisure data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/leisure?country=Australia&abbreviation=AUD&page=1'
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
        get_response = client.get('/v1/leisure?city=Perth&abbreviation=AUD',
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
        get_first_page_response = client.get('/v1/leisure',
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
        get_second_page_response = client.get('/v1/leisure?page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['leisure data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/leisure?page=1'
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
        get_response = client.get('/v1/leisure?city=Perth',
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
        get_first_page_response = client.get('/v1/leisure?abbreviation=AUD',
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
        get_second_page_response = client.get('/v1/leisure?abbreviation=AUD&page=2',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_second_page_response_data = json.loads(get_second_page_response.get_data(as_text = True))
        assert len(get_second_page_response_data['leisure data']) == 0
        assert get_second_page_response_data['previous'] != None
        assert get_second_page_response_data['previous'] == 'http://127.0.0.1/v1/leisure?abbreviation=AUD&page=1'
        assert get_second_page_response_data['next'] == None
        assert get_second_page_response.status_code == HttpStatus.ok_200.value