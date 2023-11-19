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
        assert len(get_response_data['home purchase data']) == 2
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
        assert len(get_response_data['home purchase data']) == 2
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
        assert len(get_response_data['home purchase data']) == 1
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
    def test_rent_get_with_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_response = client.get('/v1/rent/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['property_location'] == 'City Centre'
        assert get_response_data['bedrooms'] == 1
        assert get_response_data['monthly_price'] == 1635.1
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_response = client.get('/v1/rent/9',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_rent_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        delete_response = client.delete('/v1/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Rent id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Rent.query.count() == 7

    def test_rent_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Rent.query.count() == 0
    
    def test_rent_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        delete_response = client.delete('/v1/rent/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestRentListResource:
    def test_rent_post_rent_location_notexist(self, client, mock_environment_variables, mock_boto3_s3):
        response = create_rent(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Rent.query.count() == 0
    
    def test_rent_post_rent_no_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/rent',
        headers = {'Content-Type': 'application/json'})
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.bad_request_400.value
        assert response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
        assert Rent.query.count() == 0
    
    def test_rent_post_rent_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/rent',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert Rent.query.count() == 0

    def test_rent_post_rent_with_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = create_rent(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == f'Successfully added 8 rent records'
        assert Rent.query.count() == 8
    
    def test_rent_patch_updated_data(self, client, create_user, login, mock_environment_variables, mock_boto3_s3, mock_boto3_s3_patch_modified, current_date):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        patch_response = client.patch('/v1/rent',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'admin': os.environ.get('ADMIN_KEY')
            }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 4 rent records'
        get_response = client.get('/v1/rent',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['rental data']) == 8
        assert get_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_response_data['rental data'][0]['monthly_price'] == 1756.41
        assert get_response_data['rental data'][0]['bedrooms'] == 1
        assert get_response_data['rental data'][0]['location']['id'] == 1
        assert get_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_response_data['rental data'][0]['location']['city'] == 'Perth'
        assert get_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_response_data['rental data'][1]['monthly_price'] == 2315.7
        assert get_response_data['rental data'][1]['bedrooms'] == 1
        assert get_response_data['rental data'][1]['location']['id'] == 2
        assert get_response_data['rental data'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['rental data'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['rental data'][2]['property_location'] == 'City Centre'
        assert get_response_data['rental data'][2]['monthly_price'] == 2588.74
        assert get_response_data['rental data'][2]['bedrooms'] == 3
        assert get_response_data['rental data'][2]['location']['id'] == 1
        assert get_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_response_data['rental data'][2]['location']['city'] == 'Perth'
        assert get_response_data['rental data'][3]['property_location'] == 'City Centre'
        assert get_response_data['rental data'][3]['monthly_price'] == 4608.27
        assert get_response_data['rental data'][3]['bedrooms'] == 3
        assert get_response_data['rental data'][3]['location']['id'] == 2
        assert get_response_data['rental data'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['rental data'][3]['location']['city'] == 'Hong Kong'
        assert get_response_data['rental data'][4]['property_location'] == 'Outside City Centre'
        assert get_response_data['rental data'][4]['monthly_price'] == 1285.83
        assert get_response_data['rental data'][4]['bedrooms'] == 1
        assert get_response_data['rental data'][4]['location']['id'] == 1
        assert get_response_data['rental data'][4]['location']['country'] == 'Australia'
        assert get_response_data['rental data'][4]['location']['city'] == 'Perth'
        assert get_response_data['rental data'][5]['property_location'] == 'Outside City Centre'
        assert get_response_data['rental data'][5]['monthly_price'] == 1663.1
        assert get_response_data['rental data'][5]['bedrooms'] == 1
        assert get_response_data['rental data'][5]['location']['id'] == 2
        assert get_response_data['rental data'][5]['location']['country'] == 'Hong Kong'
        assert get_response_data['rental data'][5]['location']['city'] == 'Hong Kong'
        assert get_response_data['rental data'][6]['property_location'] == 'Outside City Centre'
        assert get_response_data['rental data'][6]['monthly_price'] == 1885.67
        assert get_response_data['rental data'][6]['bedrooms'] == 3
        assert get_response_data['rental data'][6]['location']['id'] == 1
        assert get_response_data['rental data'][6]['location']['country'] == 'Australia'
        assert get_response_data['rental data'][6]['location']['city'] == 'Perth'
        assert get_response_data['rental data'][7]['property_location'] == 'Outside City Centre'
        assert get_response_data['rental data'][7]['monthly_price'] == 2953.79
        assert get_response_data['rental data'][7]['bedrooms'] == 3
        assert get_response_data['rental data'][7]['location']['id'] == 2
        assert get_response_data['rental data'][7]['location']['country'] == 'Hong Kong'
        assert get_response_data['rental data'][7]['location']['city'] == 'Hong Kong'
        assert get_response.status_code == HttpStatus.ok_200.value
    
    def test_rent_patch_no_updated_data(self, client, create_user, login, mock_environment_variables, mock_boto3_s3, current_date):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        patch_response = client.patch('/v1/rent',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
            'admin': os.environ.get('ADMIN_KEY')
            }))
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 0 rent records'
        get_response = client.get('/v1/rent',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['rental data']) == 8
        assert get_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_response_data['rental data'][0]['monthly_price'] == 1635.1
        assert get_response_data['rental data'][0]['bedrooms'] == 1
        assert get_response_data['rental data'][0]['location']['id'] == 1
        assert get_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_response_data['rental data'][0]['location']['city'] == 'Perth'
        assert get_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_response_data['rental data'][1]['monthly_price'] == 2315.7
        assert get_response_data['rental data'][1]['bedrooms'] == 1
        assert get_response_data['rental data'][1]['location']['id'] == 2
        assert get_response_data['rental data'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['rental data'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['rental data'][2]['property_location'] == 'City Centre'
        assert get_response_data['rental data'][2]['monthly_price'] == 2454.62
        assert get_response_data['rental data'][2]['bedrooms'] == 3
        assert get_response_data['rental data'][2]['location']['id'] == 1
        assert get_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_response_data['rental data'][2]['location']['city'] == 'Perth'
        assert get_response_data['rental data'][3]['property_location'] == 'City Centre'
        assert get_response_data['rental data'][3]['monthly_price'] == 4608.27
        assert get_response_data['rental data'][3]['bedrooms'] == 3
        assert get_response_data['rental data'][3]['location']['id'] == 2
        assert get_response_data['rental data'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['rental data'][3]['location']['city'] == 'Hong Kong'
        assert get_response_data['rental data'][4]['property_location'] == 'Outside City Centre'
        assert get_response_data['rental data'][4]['monthly_price'] == 1191.26
        assert get_response_data['rental data'][4]['bedrooms'] == 1
        assert get_response_data['rental data'][4]['location']['id'] == 1
        assert get_response_data['rental data'][4]['location']['country'] == 'Australia'
        assert get_response_data['rental data'][4]['location']['city'] == 'Perth'
        assert get_response_data['rental data'][5]['property_location'] == 'Outside City Centre'
        assert get_response_data['rental data'][5]['monthly_price'] == 1663.1
        assert get_response_data['rental data'][5]['bedrooms'] == 1
        assert get_response_data['rental data'][5]['location']['id'] == 2
        assert get_response_data['rental data'][5]['location']['country'] == 'Hong Kong'
        assert get_response_data['rental data'][5]['location']['city'] == 'Hong Kong'
        assert get_response_data['rental data'][6]['property_location'] == 'Outside City Centre'
        assert get_response_data['rental data'][6]['monthly_price'] == 1763.16
        assert get_response_data['rental data'][6]['bedrooms'] == 3
        assert get_response_data['rental data'][6]['location']['id'] == 1
        assert get_response_data['rental data'][6]['location']['country'] == 'Australia'
        assert get_response_data['rental data'][6]['location']['city'] == 'Perth'
        assert get_response_data['rental data'][7]['property_location'] == 'Outside City Centre'
        assert get_response_data['rental data'][7]['monthly_price'] == 2953.79
        assert get_response_data['rental data'][7]['bedrooms'] == 3
        assert get_response_data['rental data'][7]['location']['id'] == 2
        assert get_response_data['rental data'][7]['location']['country'] == 'Hong Kong'
        assert get_response_data['rental data'][7]['location']['city'] == 'Hong Kong'
        assert get_response.status_code == HttpStatus.ok_200.value
    
    def test_rent_update_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        patch_response = client.patch('/v1/rent',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_rent_patch_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        response = client.patch('/v1/rent',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_rent_get_country_city_abbreviation(self, client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_response = client.get('/v1/rent?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['rental data']) == 4
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['bedrooms'] == 1
        assert get_response_data[0]['monthly_price'] == 2534.4
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['property_location'] == 'City Centre'
        assert get_response_data[1]['bedrooms'] == 3
        assert get_response_data[1]['monthly_price'] == 3804.66
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['property_location'] == 'Outside City Centre'
        assert get_response_data[2]['bedrooms'] == 1
        assert get_response_data[2]['monthly_price'] == 1846.45
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['property_location'] == 'Outside City Centre'
        assert get_response_data[3]['bedrooms'] == 3
        assert get_response_data[3]['monthly_price'] == 2732.9
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_country_city_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_response = client.get('/v1/rent?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['rental data']) == 4
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['bedrooms'] == 1
        assert get_response_data[0]['monthly_price'] == 1635.1
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['property_location'] == 'City Centre'
        assert get_response_data[1]['bedrooms'] == 3
        assert get_response_data[1]['monthly_price'] == 2454.62
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['property_location'] == 'Outside City Centre'
        assert get_response_data[2]['bedrooms'] == 1
        assert get_response_data[2]['monthly_price'] == 1191.26
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['property_location'] == 'Outside City Centre'
        assert get_response_data[3]['bedrooms'] == 3
        assert get_response_data[3]['monthly_price'] == 1763.16
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_country_city_none_abbreviation_none(self,client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/rent?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['rental data']) == 4
        assert get_first_page_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][0]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][0]['monthly_price'] == 1635.1
        assert get_first_page_response_data['rental data'][0]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][1]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][1]['monthly_price'] == 2454.62
        assert get_first_page_response_data['rental data'][1]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][2]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][2]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][2]['monthly_price'] == 1191.26
        assert get_first_page_response_data['rental data'][2]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][3]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][3]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][3]['monthly_price'] == 1763.16
        assert get_first_page_response_data['rental data'][3]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 4
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

    def test_rent_get_country_abbreviation_city_none(self,client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/rent?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['rental data']) == 4
        assert get_first_page_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][0]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][0]['monthly_price'] == 2534.4
        assert get_first_page_response_data['rental data'][0]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][1]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][1]['monthly_price'] == 3804.66
        assert get_first_page_response_data['rental data'][1]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][2]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][2]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][2]['monthly_price'] == 1846.45
        assert get_first_page_response_data['rental data'][2]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][3]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][3]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][3]['monthly_price'] == 2732.9
        assert get_first_page_response_data['rental data'][3]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 4
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

    def test_rent_get_city_abbreviation_country_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_response = client.get('/v1/rent?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['rental data']) == 4
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['bedrooms'] == 1
        assert get_response_data[0]['monthly_price'] == 2534.4
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['property_location'] == 'City Centre'
        assert get_response_data[1]['bedrooms'] == 3
        assert get_response_data[1]['monthly_price'] == 3804.66
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['property_location'] == 'Outside City Centre'
        assert get_response_data[2]['bedrooms'] == 1
        assert get_response_data[2]['monthly_price'] == 1846.45
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['property_location'] == 'Outside City Centre'
        assert get_response_data[3]['bedrooms'] == 3
        assert get_response_data[3]['monthly_price'] == 2732.9
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_country_none_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/rent',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['rental data']) == 8
        assert get_first_page_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][0]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][0]['monthly_price'] == 1635.1
        assert get_first_page_response_data['rental data'][0]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][1]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][1]['monthly_price'] == 2315.70
        assert get_first_page_response_data['rental data'][1]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][2]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][2]['monthly_price'] == 2454.62
        assert get_first_page_response_data['rental data'][2]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][3]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][3]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][3]['monthly_price'] == 4608.27
        assert get_first_page_response_data['rental data'][3]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][3]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][4]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][4]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][4]['monthly_price'] == 1191.26
        assert get_first_page_response_data['rental data'][4]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][4]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][4]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][5]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][5]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][5]['monthly_price'] == 1663.1
        assert get_first_page_response_data['rental data'][5]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][5]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][5]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][6]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][6]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][6]['monthly_price'] == 1763.16
        assert get_first_page_response_data['rental data'][6]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][6]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][6]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][7]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][7]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][7]['monthly_price'] == 2953.79
        assert get_first_page_response_data['rental data'][7]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][7]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][7]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['count'] == 8
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

    def test_rent_get_city_country_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_response = client.get('/v1/rent?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['property_location'] == 'City Centre'
        assert get_response_data[0]['bedrooms'] == 1
        assert get_response_data[0]['monthly_price'] == 1635.1
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['property_location'] == 'City Centre'
        assert get_response_data[1]['bedrooms'] == 3
        assert get_response_data[1]['monthly_price'] == 2454.62
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['property_location'] == 'Outside City Centre'
        assert get_response_data[2]['bedrooms'] == 1
        assert get_response_data[2]['monthly_price'] == 1191.26
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['property_location'] == 'Outside City Centre'
        assert get_response_data[3]['bedrooms'] == 3
        assert get_response_data[3]['monthly_price'] == 1763.16
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_rent_get_abbreviation_country_none_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_rent(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/rent?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['rental data']) == 8
        assert get_first_page_response_data['rental data'][0]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][0]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][0]['monthly_price'] == 2534.4
        assert get_first_page_response_data['rental data'][0]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][1]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][1]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][1]['monthly_price'] == 3589.34
        assert get_first_page_response_data['rental data'][1]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][2]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][2]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][2]['monthly_price'] == 3804.66
        assert get_first_page_response_data['rental data'][2]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][3]['property_location'] == 'City Centre'
        assert get_first_page_response_data['rental data'][3]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][3]['monthly_price'] == 7142.82
        assert get_first_page_response_data['rental data'][3]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][3]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][4]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][4]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][4]['monthly_price'] == 1846.45
        assert get_first_page_response_data['rental data'][4]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][4]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][4]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][5]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][5]['bedrooms'] == 1
        assert get_first_page_response_data['rental data'][5]['monthly_price'] == 2577.8
        assert get_first_page_response_data['rental data'][5]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][5]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][5]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][6]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][6]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][6]['monthly_price'] == 2732.9
        assert get_first_page_response_data['rental data'][6]['location']['id'] == 1
        assert get_first_page_response_data['rental data'][6]['location']['country'] == 'Australia'
        assert get_first_page_response_data['rental data'][6]['location']['city'] == 'Perth'
        assert get_first_page_response_data['rental data'][7]['property_location'] == 'Outside City Centre'
        assert get_first_page_response_data['rental data'][7]['bedrooms'] == 3
        assert get_first_page_response_data['rental data'][7]['monthly_price'] == 4578.37
        assert get_first_page_response_data['rental data'][7]['location']['id'] == 2
        assert get_first_page_response_data['rental data'][7]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['rental data'][7]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['count'] == 8
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
    def test_utilities_get_with_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_response = client.get('/v1/utilities/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data['monthly_price'] == 35.83
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_response = client.get('/v1/utilities/9',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_utilities_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        delete_response = client.delete('/v1/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Utilities id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Utilities.query.count() == 7

    def test_utilities_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Utilities.query.count() == 0
    
    def test_utilities_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        delete_response = client.delete('/v1/utilities/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestUtilitiesListResource:
    def test_utilities_post_utilities_location_notexist(self,client, mock_environment_variables, mock_boto3_s3):
        response = create_utilities(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Utilities.query.count() == 0
    
    def test_utilities_post_utilities_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/utilities',
        headers = {'Content-Type': 'application/json'})
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.bad_request_400.value
        assert response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
        assert Utilities.query.count() == 0
    
    def test_utilities_post_utilities_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/utilities',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert Utilities.query.count() == 0

    def test_utilities_post_utilities_with_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = create_utilities(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == f'Successfully added 8 utilities records'
        assert Utilities.query.count() == 8
    
    def test_utilities_patch_updated_data(self,client,create_user,login, mock_environment_variables, mock_boto3_s3, mock_boto3_s3_patch_modified):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        patch_response = utilities_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 2 utilities records'
        get_response = client.get('/v1/utilities',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['utilities']) == 8
        assert get_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_response_data['utilities'][0]['monthly_price'] == 125
        assert get_response_data['utilities'][0]['location']['id'] == 1
        assert get_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_response_data['utilities'][0]['location']['city'] == 'Perth'
        assert get_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_response_data['utilities'][1]['monthly_price'] == 146
        assert get_response_data['utilities'][1]['location']['id'] == 2
        assert get_response_data['utilities'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['utilities'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['utilities'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_response_data['utilities'][2]['monthly_price'] == 217
        assert get_response_data['utilities'][2]['location']['id'] == 1
        assert get_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_response_data['utilities'][3]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_response_data['utilities'][3]['monthly_price'] == 223
        assert get_response_data['utilities'][3]['location']['id'] == 2
        assert get_response_data['utilities'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['utilities'][3]['location']['city'] == 'Hong Kong'
        assert get_response_data['utilities'][4]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_response_data['utilities'][4]['monthly_price'] == 23.51
        assert get_response_data['utilities'][4]['location']['id'] == 2
        assert get_response_data['utilities'][4]['location']['country'] == 'Hong Kong'
        assert get_response_data['utilities'][4]['location']['city'] == 'Hong Kong'
        assert get_response_data['utilities'][5]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_response_data['utilities'][5]['monthly_price'] == 62.97
        assert get_response_data['utilities'][5]['location']['id'] == 1
        assert get_response_data['utilities'][5]['location']['country'] == 'Australia'
        assert get_response_data['utilities'][5]['location']['city'] == 'Perth'
        assert get_response_data['utilities'][6]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data['utilities'][6]['monthly_price'] == 19.08
        assert get_response_data['utilities'][6]['location']['id'] == 2
        assert get_response_data['utilities'][6]['location']['country'] == 'Hong Kong'
        assert get_response_data['utilities'][6]['location']['city'] == 'Hong Kong'
        assert get_response_data['utilities'][7]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data['utilities'][7]['monthly_price'] == 36.14
        assert get_response_data['utilities'][7]['location']['id'] == 1
        assert get_response_data['utilities'][7]['location']['country'] == 'Australia'
        assert get_response_data['utilities'][7]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value
    
    def test_utilities_patch_no_updated_data(self, client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        patch_response = utilities_patch_updated_data(client, mock_environment_variables, mock_boto3_s3)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 0 utilities records'
        get_response = client.get('/v1/utilities',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['utilities']) == 8
        assert get_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_response_data['utilities'][0]['monthly_price'] == 124
        assert get_response_data['utilities'][0]['location']['id'] == 1
        assert get_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_response_data['utilities'][0]['location']['city'] == 'Perth'
        assert get_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_response_data['utilities'][1]['monthly_price'] == 146
        assert get_response_data['utilities'][1]['location']['id'] == 2
        assert get_response_data['utilities'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['utilities'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['utilities'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_response_data['utilities'][2]['monthly_price'] == 216
        assert get_response_data['utilities'][2]['location']['id'] == 1
        assert get_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_response_data['utilities'][3]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_response_data['utilities'][3]['monthly_price'] == 223
        assert get_response_data['utilities'][3]['location']['id'] == 2
        assert get_response_data['utilities'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['utilities'][3]['location']['city'] == 'Hong Kong'
        assert get_response_data['utilities'][4]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_response_data['utilities'][4]['monthly_price'] == 23.51
        assert get_response_data['utilities'][4]['location']['id'] == 2
        assert get_response_data['utilities'][4]['location']['country'] == 'Hong Kong'
        assert get_response_data['utilities'][4]['location']['city'] == 'Hong Kong'
        assert get_response_data['utilities'][5]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_response_data['utilities'][5]['monthly_price'] == 62.23
        assert get_response_data['utilities'][5]['location']['id'] == 1
        assert get_response_data['utilities'][5]['location']['country'] == 'Australia'
        assert get_response_data['utilities'][5]['location']['city'] == 'Perth'
        assert get_response_data['utilities'][6]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data['utilities'][6]['monthly_price'] == 19.08
        assert get_response_data['utilities'][6]['location']['id'] == 2
        assert get_response_data['utilities'][6]['location']['country'] == 'Hong Kong'
        assert get_response_data['utilities'][6]['location']['city'] == 'Hong Kong'
        assert get_response_data['utilities'][7]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data['utilities'][7]['monthly_price'] == 35.83
        assert get_response_data['utilities'][7]['location']['id'] == 1
        assert get_response_data['utilities'][7]['location']['country'] == 'Australia'
        assert get_response_data['utilities'][7]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value
    
    def test_utilities_patch_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        patch_response = client.patch('/v1/utilities',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_utilities_patch_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        response = client.patch('/v1/utilities',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_utilities_get_country_city_abbreviation(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_response = client.get('/v1/utilities?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_response_data[0]['monthly_price'] == 192.2
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_response_data[1]['monthly_price'] == 334.8
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_response_data[2]['monthly_price'] == 96.46
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data[3]['monthly_price'] == 55.54
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_country_city_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_response = client.get('/v1/utilities?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_response_data[0]['monthly_price'] == 124
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_response_data[1]['monthly_price'] == 216
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_response_data[2]['monthly_price'] == 62.23
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data[3]['monthly_price'] == 35.83
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_country_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/utilities?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['utilities']) == 4
        assert get_first_page_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_first_page_response_data['utilities'][0]['monthly_price'] == 124
        assert get_first_page_response_data['utilities'][0]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_first_page_response_data['utilities'][1]['monthly_price'] == 216
        assert get_first_page_response_data['utilities'][1]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][2]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_first_page_response_data['utilities'][2]['monthly_price'] == 62.23
        assert get_first_page_response_data['utilities'][2]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][3]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_first_page_response_data['utilities'][3]['monthly_price'] == 35.83
        assert get_first_page_response_data['utilities'][3]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 4
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

    def test_utilities_get_country_abbreviation_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/utilities?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['utilities']) == 4
        assert get_first_page_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_first_page_response_data['utilities'][0]['monthly_price'] == 192.2
        assert get_first_page_response_data['utilities'][0]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_first_page_response_data['utilities'][1]['monthly_price'] == 334.8
        assert get_first_page_response_data['utilities'][1]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][2]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_first_page_response_data['utilities'][2]['monthly_price'] == 96.46
        assert get_first_page_response_data['utilities'][2]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][3]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_first_page_response_data['utilities'][3]['monthly_price'] == 55.54
        assert get_first_page_response_data['utilities'][3]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 4
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

    def test_utilities_get_city_abbreviation_country_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_response = client.get('/v1/utilities?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_response_data[0]['monthly_price'] == 192.2
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_response_data[1]['monthly_price'] == 334.8
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_response_data[2]['monthly_price'] == 96.46
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data[3]['monthly_price'] == 55.54
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_country_none_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/utilities',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['utilities']) == 8
        assert get_first_page_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_first_page_response_data['utilities'][0]['monthly_price'] == 124
        assert get_first_page_response_data['utilities'][0]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_first_page_response_data['utilities'][1]['monthly_price'] == 146
        assert get_first_page_response_data['utilities'][1]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_first_page_response_data['utilities'][2]['monthly_price'] == 216
        assert get_first_page_response_data['utilities'][2]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][3]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_first_page_response_data['utilities'][3]['monthly_price'] == 223
        assert get_first_page_response_data['utilities'][3]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][3]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][4]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_first_page_response_data['utilities'][4]['monthly_price'] == 23.51
        assert get_first_page_response_data['utilities'][4]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][4]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][4]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][5]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_first_page_response_data['utilities'][5]['monthly_price'] == 62.23
        assert get_first_page_response_data['utilities'][5]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][5]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][5]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][6]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_first_page_response_data['utilities'][6]['monthly_price'] == 19.08
        assert get_first_page_response_data['utilities'][6]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][6]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][6]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][7]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_first_page_response_data['utilities'][7]['monthly_price'] == 35.83
        assert get_first_page_response_data['utilities'][7]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][7]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][7]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 8
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

    def test_utilities_get_city_country_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_response = client.get('/v1/utilities?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_response_data[0]['monthly_price'] == 124
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_response_data[1]['monthly_price'] == 216
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_response_data[2]['monthly_price'] == 62.23
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_response_data[3]['monthly_price'] == 35.83
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_utilities_get_abbreviation_country_none_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_utilities(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/utilities?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        print(get_first_page_response_data)
        assert len(get_first_page_response_data['utilities']) == 8
        assert get_first_page_response_data['utilities'][0]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_first_page_response_data['utilities'][0]['monthly_price'] == 192.2
        assert get_first_page_response_data['utilities'][0]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][1]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (1 Person)'
        assert get_first_page_response_data['utilities'][1]['monthly_price'] == 226.3
        assert get_first_page_response_data['utilities'][1]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][2]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_first_page_response_data['utilities'][2]['monthly_price'] == 334.8
        assert get_first_page_response_data['utilities'][2]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][3]['utility'] == 'Electricity, Heating, Cooling, Water and Garbage (Family)'
        assert get_first_page_response_data['utilities'][3]['monthly_price'] == 345.65
        assert get_first_page_response_data['utilities'][3]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][3]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][4]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_first_page_response_data['utilities'][4]['monthly_price'] == 36.44
        assert get_first_page_response_data['utilities'][4]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][4]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][4]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][5]['utility'] == 'Internet (60 Mbps, Unlimited Data, Monthly)'
        assert get_first_page_response_data['utilities'][5]['monthly_price'] == 96.46
        assert get_first_page_response_data['utilities'][5]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][5]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][5]['location']['city'] == 'Perth'
        assert get_first_page_response_data['utilities'][6]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_first_page_response_data['utilities'][6]['monthly_price'] == 29.57
        assert get_first_page_response_data['utilities'][6]['location']['id'] == 2
        assert get_first_page_response_data['utilities'][6]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][6]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['utilities'][7]['utility'] == 'Mobile Plan (10GB+ Data, Monthly)'
        assert get_first_page_response_data['utilities'][7]['monthly_price'] == 55.54
        assert get_first_page_response_data['utilities'][7]['location']['id'] == 1
        assert get_first_page_response_data['utilities'][7]['location']['country'] == 'Australia'
        assert get_first_page_response_data['utilities'][7]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 8
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
    def test_transportation_get_with_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_response = client.get('/v1/transportation/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data['price'] == 2.9
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_response = client.get('/v1/transportation/9',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_transportation_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        delete_response = client.delete('/v1/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Transportation id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Transportation.query.count() == 7

    def test_transportation_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Transportation.query.count() == 0
    
    def test_transportation_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        delete_response = client.delete('/v1/transportation/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestTransportationListResource:
    def test_transportation_post_transportation_location_notexist(self,client, mock_environment_variables, mock_boto3_s3):
        response = create_transportation(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Transportation.query.count() == 0
    
    def test_transportation_post_transportation_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        response = client.post('/v1/transportation',
        headers = {'Content-Type': 'application/json'})
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.bad_request_400.value
        assert response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_transportation_post_transportation_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/transportation',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert Transportation.query.count() == 0

    def test_transportation_post_transportation_with_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = create_transportation(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == f'Successfully added 8 transportation records'
        assert Transportation.query.count() == 8
    
    def test_transportation_patch_updated_data(self,client,create_user,login, mock_environment_variables, mock_boto3_s3_patch_modified):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        patch_response = transportation_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 4 transportation records'
        get_response = client.get('/v1/transportation',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response.status_code == HttpStatus.ok_200.value
        assert len(get_response_data['transportation data']) == 8
        assert get_response_data['transportation data'][0]['type'] == 'Petrol (1L)'
        assert get_response_data['transportation data'][0]['price'] == 1.3
        assert get_response_data['transportation data'][0]['location']['id'] == 1
        assert get_response_data['transportation data'][0]['location']['country'] == 'Australia'
        assert get_response_data['transportation data'][0]['location']['city'] == 'Perth'
        assert get_response_data['transportation data'][1]['type'] == 'Petrol (1L)'
        assert get_response_data['transportation data'][1]['price'] == 2.88
        assert get_response_data['transportation data'][1]['location']['id'] == 2
        assert get_response_data['transportation data'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['transportation data'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['transportation data'][2]['type'] == 'Public Transport (Monthly)'
        assert get_response_data['transportation data'][2]['price'] == 63.9
        assert get_response_data['transportation data'][2]['location']['id'] == 2
        assert get_response_data['transportation data'][2]['location']['country'] == 'Hong Kong'
        assert get_response_data['transportation data'][2]['location']['city'] == 'Hong Kong'
        assert get_response_data['transportation data'][3]['type'] == 'Public Transport (Monthly)'
        assert get_response_data['transportation data'][3]['price'] == 114.13
        assert get_response_data['transportation data'][3]['location']['id'] == 1
        assert get_response_data['transportation data'][3]['location']['country'] == 'Australia'
        assert get_response_data['transportation data'][3]['location']['city'] == 'Perth'
        assert get_response_data['transportation data'][4]['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data['transportation data'][4]['price'] == 1.53
        assert get_response_data['transportation data'][4]['location']['id'] == 2
        assert get_response_data['transportation data'][4]['location']['country'] == 'Hong Kong'
        assert get_response_data['transportation data'][4]['location']['city'] == 'Hong Kong'
        assert get_response_data['transportation data'][5]['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data['transportation data'][5]['price'] == 2.94
        assert get_response_data['transportation data'][5]['location']['id'] == 1
        assert get_response_data['transportation data'][5]['location']['country'] == 'Australia'
        assert get_response_data['transportation data'][5]['location']['city'] == 'Perth'
        assert get_response_data['transportation data'][6]['type'] == 'Taxi (8km)'
        assert get_response_data['transportation data'][6]['price'] == 13.0
        assert get_response_data['transportation data'][6]['location']['id'] == 2
        assert get_response_data['transportation data'][6]['location']['country'] == 'Hong Kong'
        assert get_response_data['transportation data'][6]['location']['city'] == 'Hong Kong'
        assert get_response_data['transportation data'][7]['type'] == 'Taxi (8km)'
        assert get_response_data['transportation data'][7]['price'] == 17.41
        assert get_response_data['transportation data'][7]['location']['id'] == 1
        assert get_response_data['transportation data'][7]['location']['country'] == 'Australia'
        assert get_response_data['transportation data'][7]['location']['city'] == 'Perth'
    
    def test_transportation_patch_no_updated_data(self, client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        patch_response = transportation_patch_updated_data(client, mock_environment_variables, mock_boto3_s3)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 0 transportation records'
        get_response = client.get('/v1/transportation',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response.status_code == HttpStatus.ok_200.value
        assert len(get_response_data['transportation data']) == 8
        assert get_response_data['transportation data'][0]['type'] == 'Petrol (1L)'
        assert get_response_data['transportation data'][0]['price'] == 1.26
        assert get_response_data['transportation data'][0]['location']['id'] == 1
        assert get_response_data['transportation data'][0]['location']['country'] == 'Australia'
        assert get_response_data['transportation data'][0]['location']['city'] == 'Perth'
        assert get_response_data['transportation data'][1]['type'] == 'Petrol (1L)'
        assert get_response_data['transportation data'][1]['price'] == 2.88
        assert get_response_data['transportation data'][1]['location']['id'] == 2
        assert get_response_data['transportation data'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['transportation data'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['transportation data'][2]['type'] == 'Public Transport (Monthly)'
        assert get_response_data['transportation data'][2]['price'] == 63.9
        assert get_response_data['transportation data'][2]['location']['id'] == 2
        assert get_response_data['transportation data'][2]['location']['country'] == 'Hong Kong'
        assert get_response_data['transportation data'][2]['location']['city'] == 'Hong Kong'
        assert get_response_data['transportation data'][3]['type'] == 'Public Transport (Monthly)'
        assert get_response_data['transportation data'][3]['price'] == 112.90
        assert get_response_data['transportation data'][3]['location']['id'] == 1
        assert get_response_data['transportation data'][3]['location']['country'] == 'Australia'
        assert get_response_data['transportation data'][3]['location']['city'] == 'Perth'
        assert get_response_data['transportation data'][4]['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data['transportation data'][4]['price'] == 1.53
        assert get_response_data['transportation data'][4]['location']['id'] == 2
        assert get_response_data['transportation data'][4]['location']['country'] == 'Hong Kong'
        assert get_response_data['transportation data'][4]['location']['city'] == 'Hong Kong'
        assert get_response_data['transportation data'][5]['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data['transportation data'][5]['price'] == 2.90
        assert get_response_data['transportation data'][5]['location']['id'] == 1
        assert get_response_data['transportation data'][5]['location']['country'] == 'Australia'
        assert get_response_data['transportation data'][5]['location']['city'] == 'Perth'
        assert get_response_data['transportation data'][6]['type'] == 'Taxi (8km)'
        assert get_response_data['transportation data'][6]['price'] == 13.0
        assert get_response_data['transportation data'][6]['location']['id'] == 2
        assert get_response_data['transportation data'][6]['location']['country'] == 'Hong Kong'
        assert get_response_data['transportation data'][6]['location']['city'] == 'Hong Kong'
        assert get_response_data['transportation data'][7]['type'] == 'Taxi (8km)'
        assert get_response_data['transportation data'][7]['price'] == 17.4
        assert get_response_data['transportation data'][7]['location']['id'] == 1
        assert get_response_data['transportation data'][7]['location']['country'] == 'Australia'
        assert get_response_data['transportation data'][7]['location']['city'] == 'Perth'

    def test_transportation_patch_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        patch_response = client.patch('/v1/transportation',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_transportation_patch_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        response = client.patch('/v1/transportation',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_transportation_get_country_city_abbreviation(self,client,create_user,login,mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_response = client.get('/v1/transportation?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['type'] == 'Petrol (1L)'
        assert get_response_data[0]['price'] == 1.95
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['type'] == 'Public Transport (Monthly)'
        assert get_response_data[1]['price'] == 175
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data[2]['price'] == 4.5
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['type'] == 'Taxi (8km)'
        assert get_response_data[3]['price'] == 26.97
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_country_city_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_response = client.get('/v1/transportation?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['type'] == 'Petrol (1L)'
        assert get_response_data[0]['price'] == 1.26
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['type'] == 'Public Transport (Monthly)'
        assert get_response_data[1]['price'] == 112.9
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data[2]['price'] == 2.9
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['type'] == 'Taxi (8km)'
        assert get_response_data[3]['price'] == 17.4
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_country_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/transportation?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['transportation data']) == 4
        assert get_first_page_response_data['transportation data'][0]['type'] == 'Petrol (1L)'
        assert get_first_page_response_data['transportation data'][0]['price'] == 1.26
        assert get_first_page_response_data['transportation data'][0]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][1]['type'] == 'Public Transport (Monthly)'
        assert get_first_page_response_data['transportation data'][1]['price'] == 112.9
        assert get_first_page_response_data['transportation data'][1]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][2]['type'] == 'Public Transport (One Way Ticket)'
        assert get_first_page_response_data['transportation data'][2]['price'] == 2.9
        assert get_first_page_response_data['transportation data'][2]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][3]['type'] == 'Taxi (8km)'
        assert get_first_page_response_data['transportation data'][3]['price'] == 17.4
        assert get_first_page_response_data['transportation data'][3]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 4
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

    def test_transportation_get_country_abbreviation_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/transportation?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['transportation data']) == 4
        assert get_first_page_response_data['transportation data'][0]['type'] == 'Petrol (1L)'
        assert get_first_page_response_data['transportation data'][0]['price'] == 1.95
        assert get_first_page_response_data['transportation data'][0]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][1]['type'] == 'Public Transport (Monthly)'
        assert get_first_page_response_data['transportation data'][1]['price'] == 175.0
        assert get_first_page_response_data['transportation data'][1]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][2]['type'] == 'Public Transport (One Way Ticket)'
        assert get_first_page_response_data['transportation data'][2]['price'] == 4.5
        assert get_first_page_response_data['transportation data'][2]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][3]['type'] == 'Taxi (8km)'
        assert get_first_page_response_data['transportation data'][3]['price'] == 26.97
        assert get_first_page_response_data['transportation data'][3]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 4
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

    def test_transportation_get_city_abbreviation_country_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_response = client.get('/v1/transportation?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['type'] == 'Petrol (1L)'
        assert get_response_data[0]['price'] == 1.95
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['type'] == 'Public Transport (Monthly)'
        assert get_response_data[1]['price'] == 175
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data[2]['price'] == 4.5
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['type'] == 'Taxi (8km)'
        assert get_response_data[3]['price'] == 26.97
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_country_none_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/transportation',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['transportation data']) == 8
        assert get_first_page_response_data['transportation data'][0]['type'] == 'Petrol (1L)'
        assert get_first_page_response_data['transportation data'][0]['price'] == 1.26
        assert get_first_page_response_data['transportation data'][0]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][1]['type'] == 'Petrol (1L)'
        assert get_first_page_response_data['transportation data'][1]['price'] == 2.88
        assert get_first_page_response_data['transportation data'][1]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][2]['type'] == 'Public Transport (Monthly)'
        assert get_first_page_response_data['transportation data'][2]['price'] == 63.9
        assert get_first_page_response_data['transportation data'][2]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][2]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][2]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][3]['type'] == 'Public Transport (Monthly)'
        assert get_first_page_response_data['transportation data'][3]['price'] == 112.90
        assert get_first_page_response_data['transportation data'][3]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][4]['type'] == 'Public Transport (One Way Ticket)'
        assert get_first_page_response_data['transportation data'][4]['price'] == 1.53
        assert get_first_page_response_data['transportation data'][4]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][4]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][4]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][5]['type'] == 'Public Transport (One Way Ticket)'
        assert get_first_page_response_data['transportation data'][5]['price'] == 2.90
        assert get_first_page_response_data['transportation data'][5]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][5]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][5]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][6]['type'] == 'Taxi (8km)'
        assert get_first_page_response_data['transportation data'][6]['price'] == 13.0
        assert get_first_page_response_data['transportation data'][6]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][6]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][6]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][7]['type'] == 'Taxi (8km)'
        assert get_first_page_response_data['transportation data'][7]['price'] == 17.4
        assert get_first_page_response_data['transportation data'][7]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][7]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][7]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 8
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

    def test_transportation_get_city_country_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_response = client.get('/v1/transportation?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 4
        assert get_response_data[0]['type'] == 'Petrol (1L)'
        assert get_response_data[0]['price'] == 1.26
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['type'] == 'Public Transport (Monthly)'
        assert get_response_data[1]['price'] == 112.9
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['type'] == 'Public Transport (One Way Ticket)'
        assert get_response_data[2]['price'] == 2.9
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['type'] == 'Taxi (8km)'
        assert get_response_data[3]['price'] == 17.4
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_transportation_get_abbreviation_country_none_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_transportation(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/transportation?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['transportation data']) == 8
        assert get_first_page_response_data['transportation data'][0]['type'] == 'Petrol (1L)'
        assert get_first_page_response_data['transportation data'][0]['price'] == 1.95
        assert get_first_page_response_data['transportation data'][0]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][1]['type'] == 'Petrol (1L)'
        assert get_first_page_response_data['transportation data'][1]['price'] == 4.46
        assert get_first_page_response_data['transportation data'][1]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][2]['type'] == 'Public Transport (Monthly)'
        assert get_first_page_response_data['transportation data'][2]['price'] == 99.05
        assert get_first_page_response_data['transportation data'][2]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][2]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][2]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][3]['type'] == 'Public Transport (Monthly)'
        assert get_first_page_response_data['transportation data'][3]['price'] == 175
        assert get_first_page_response_data['transportation data'][3]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][4]['type'] == 'Public Transport (One Way Ticket)'
        assert get_first_page_response_data['transportation data'][4]['price'] == 2.37
        assert get_first_page_response_data['transportation data'][4]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][4]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][4]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][5]['type'] == 'Public Transport (One Way Ticket)'
        assert get_first_page_response_data['transportation data'][5]['price'] == 4.5
        assert get_first_page_response_data['transportation data'][5]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][5]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][5]['location']['city'] == 'Perth'
        assert get_first_page_response_data['transportation data'][6]['type'] == 'Taxi (8km)'
        assert get_first_page_response_data['transportation data'][6]['price'] == 20.15
        assert get_first_page_response_data['transportation data'][6]['location']['id'] == 2
        assert get_first_page_response_data['transportation data'][6]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][6]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['transportation data'][7]['type'] == 'Taxi (8km)'
        assert get_first_page_response_data['transportation data'][7]['price'] == 26.97
        assert get_first_page_response_data['transportation data'][7]['location']['id'] == 1
        assert get_first_page_response_data['transportation data'][7]['location']['country'] == 'Australia'
        assert get_first_page_response_data['transportation data'][7]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 8
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
    def test_foodbeverage_get_with_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_response = client.get('/v1/foodbeverage/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        print(get_response_data)
        assert get_response_data['item_category'] == 'Beverage'
        assert get_response_data['purchase_point'] == 'Restaurant'
        assert get_response_data['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data['price'] == 7.41
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_response = client.get('/v1/foodbeverage/11',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_foodbeverage_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        delete_response = client.delete('/v1/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'FoodBeverage id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert FoodBeverage.query.count() == 9

    def test_foodbeverage_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert FoodBeverage.query.count() == 0
    
    def test_foodbeverage_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        delete_response = client.delete('/v1/foodbeverage/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'
    
class TestFoodBeverageListResource:
    def test_foodbeverage_post_foodbeverage_location_notexist(self,client, mock_environment_variables, mock_boto3_s3):
        response = create_foodbeverage(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert FoodBeverage.query.count() == 0
    
    def test_foodbeverage_post_foodbeverage_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        response = client.post('/v1/foodbeverage',
        headers = {'Content-Type': 'application/json'})
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.bad_request_400.value
        assert response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_foodbeverage_post_foodbeverage_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/foodbeverage',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert FoodBeverage.query.count() == 0

    def test_foodbeverage_post_foodbeverage_with_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = create_foodbeverage(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == f'Successfully added 10 foodbeverage records'
        assert FoodBeverage.query.count() == 10
    
    def test_foodbeverage_patch_updated_data(self,client,create_user,login, mock_environment_variables, mock_boto3_s3_patch_modified):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        patch_response = foodbeverage_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 5 foodbeverage records'
        get_response = client.get('/v1/foodbeverage',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['food and beverage data']) == 10
        assert get_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][0]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][0]['item'] == 'Cappuccino (Regular)'
        assert get_response_data['food and beverage data'][0]['price'] == 3.8
        assert get_response_data['food and beverage data'][0]['location']['id'] == 1
        assert get_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][0]['location']['city'] == 'Perth'
        assert get_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][1]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][1]['item'] == 'Cappuccino (Regular)'
        assert get_response_data['food and beverage data'][1]['price'] == 5.05
        assert get_response_data['food and beverage data'][1]['location']['id'] == 2
        assert get_response_data['food and beverage data'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][2]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][2]['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data['food and beverage data'][2]['price'] == 6.39
        assert get_response_data['food and beverage data'][2]['location']['id'] == 2
        assert get_response_data['food and beverage data'][2]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][2]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][3]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][3]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][3]['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data['food and beverage data'][3]['price'] == 7.81
        assert get_response_data['food and beverage data'][3]['location']['id'] == 1
        assert get_response_data['food and beverage data'][3]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][3]['location']['city'] == 'Perth'
        assert get_response_data['food and beverage data'][4]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][4]['purchase_point'] == 'Supermarket'
        assert get_response_data['food and beverage data'][4]['item'] == 'Milk (1L)'
        assert get_response_data['food and beverage data'][4]['price'] == 1.96
        assert get_response_data['food and beverage data'][4]['location']['id'] == 1
        assert get_response_data['food and beverage data'][4]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][4]['location']['city'] == 'Perth'
        assert get_response_data['food and beverage data'][5]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][5]['purchase_point'] == 'Supermarket'
        assert get_response_data['food and beverage data'][5]['item'] == 'Milk (1L)'
        assert get_response_data['food and beverage data'][5]['price'] == 3.08
        assert get_response_data['food and beverage data'][5]['location']['id'] == 2
        assert get_response_data['food and beverage data'][5]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][5]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][6]['item_category'] == 'Food'
        assert get_response_data['food and beverage data'][6]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][6]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_response_data['food and beverage data'][6]['price'] == 63.9
        assert get_response_data['food and beverage data'][6]['location']['id'] == 2
        assert get_response_data['food and beverage data'][6]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][6]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][7]['item_category'] == 'Food'
        assert get_response_data['food and beverage data'][7]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][7]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_response_data['food and beverage data'][7]['price'] == 97.68
        assert get_response_data['food and beverage data'][7]['location']['id'] == 1
        assert get_response_data['food and beverage data'][7]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][7]['location']['city'] == 'Perth'
        assert get_response_data['food and beverage data'][8]['item_category'] == 'Food'
        assert get_response_data['food and beverage data'][8]['purchase_point'] == 'Supermarket'
        assert get_response_data['food and beverage data'][8]['item'] == 'Bread (500g)'
        assert get_response_data['food and beverage data'][8]['price'] == 2.26
        assert get_response_data['food and beverage data'][8]['location']['id'] == 2
        assert get_response_data['food and beverage data'][8]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][8]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][9]['item_category'] == 'Food'
        assert get_response_data['food and beverage data'][9]['purchase_point'] == 'Supermarket'
        assert get_response_data['food and beverage data'][9]['item'] == 'Bread (500g)'
        assert get_response_data['food and beverage data'][9]['price'] == 2.54
        assert get_response_data['food and beverage data'][9]['location']['id'] == 1
        assert get_response_data['food and beverage data'][9]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][9]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_patch_no_updated_data(self,client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        patch_response = foodbeverage_patch_updated_data(client, mock_environment_variables, mock_boto3_s3)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 0 foodbeverage records'
        get_response = client.get('/v1/foodbeverage',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['food and beverage data']) == 10
        assert get_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][0]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][0]['item'] == 'Cappuccino (Regular)'
        assert get_response_data['food and beverage data'][0]['price'] == 3.64
        assert get_response_data['food and beverage data'][0]['location']['id'] == 1
        assert get_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][0]['location']['city'] == 'Perth'
        assert get_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][1]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][1]['item'] == 'Cappuccino (Regular)'
        assert get_response_data['food and beverage data'][1]['price'] == 5.05
        assert get_response_data['food and beverage data'][1]['location']['id'] == 2
        assert get_response_data['food and beverage data'][1]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][1]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][2]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][2]['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data['food and beverage data'][2]['price'] == 6.39
        assert get_response_data['food and beverage data'][2]['location']['id'] == 2
        assert get_response_data['food and beverage data'][2]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][2]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][3]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][3]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][3]['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data['food and beverage data'][3]['price'] == 7.41
        assert get_response_data['food and beverage data'][3]['location']['id'] == 1
        assert get_response_data['food and beverage data'][3]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][3]['location']['city'] == 'Perth'
        assert get_response_data['food and beverage data'][4]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][4]['purchase_point'] == 'Supermarket'
        assert get_response_data['food and beverage data'][4]['item'] == 'Milk (1L)'
        assert get_response_data['food and beverage data'][4]['price'] == 1.82
        assert get_response_data['food and beverage data'][4]['location']['id'] == 1
        assert get_response_data['food and beverage data'][4]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][4]['location']['city'] == 'Perth'
        assert get_response_data['food and beverage data'][5]['item_category'] == 'Beverage'
        assert get_response_data['food and beverage data'][5]['purchase_point'] == 'Supermarket'
        assert get_response_data['food and beverage data'][5]['item'] == 'Milk (1L)'
        assert get_response_data['food and beverage data'][5]['price'] == 3.08
        assert get_response_data['food and beverage data'][5]['location']['id'] == 2
        assert get_response_data['food and beverage data'][5]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][5]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][6]['item_category'] == 'Food'
        assert get_response_data['food and beverage data'][6]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][6]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_response_data['food and beverage data'][6]['price'] == 63.9
        assert get_response_data['food and beverage data'][6]['location']['id'] == 2
        assert get_response_data['food and beverage data'][6]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][6]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][7]['item_category'] == 'Food'
        assert get_response_data['food and beverage data'][7]['purchase_point'] == 'Restaurant'
        assert get_response_data['food and beverage data'][7]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_response_data['food and beverage data'][7]['price'] == 96.31
        assert get_response_data['food and beverage data'][7]['location']['id'] == 1
        assert get_response_data['food and beverage data'][7]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][7]['location']['city'] == 'Perth'
        assert get_response_data['food and beverage data'][8]['item_category'] == 'Food'
        assert get_response_data['food and beverage data'][8]['purchase_point'] == 'Supermarket'
        assert get_response_data['food and beverage data'][8]['item'] == 'Bread (500g)'
        assert get_response_data['food and beverage data'][8]['price'] == 2.26
        assert get_response_data['food and beverage data'][8]['location']['id'] == 2
        assert get_response_data['food and beverage data'][8]['location']['country'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][8]['location']['city'] == 'Hong Kong'
        assert get_response_data['food and beverage data'][9]['item_category'] == 'Food'
        assert get_response_data['food and beverage data'][9]['purchase_point'] == 'Supermarket'
        assert get_response_data['food and beverage data'][9]['item'] == 'Bread (500g)'
        assert get_response_data['food and beverage data'][9]['price'] == 2.44
        assert get_response_data['food and beverage data'][9]['location']['id'] == 1
        assert get_response_data['food and beverage data'][9]['location']['country'] == 'Australia'
        assert get_response_data['food and beverage data'][9]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value
    
    def test_foodbeverage_patch_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        patch_response = client.patch('/v1/foodbeverage',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_foodbeverage_patch_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        response = client.patch('/v1/foodbeverage',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_foodbeverage_get_country_city_abbreviation(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_response = client.get('/v1/foodbeverage?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 5
        assert get_response_data[0]['item_category'] == 'Beverage'
        assert get_response_data[0]['purchase_point'] == 'Restaurant'
        assert get_response_data[0]['item'] == 'Cappuccino (Regular)'
        assert get_response_data[0]['price'] == 5.64
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['item_category'] == 'Beverage'
        assert get_response_data[1]['purchase_point'] == 'Restaurant'
        assert get_response_data[1]['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data[1]['price'] == 11.49
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['item_category'] == 'Beverage'
        assert get_response_data[2]['purchase_point'] == 'Supermarket'
        assert get_response_data[2]['item'] == 'Milk (1L)'
        assert get_response_data[2]['price'] == 2.82
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['item_category'] == 'Food'
        assert get_response_data[3]['purchase_point'] == 'Restaurant'
        assert get_response_data[3]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_response_data[3]['price'] == 149.28
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response_data[4]['item_category'] == 'Food'
        assert get_response_data[4]['purchase_point'] == 'Supermarket'
        assert get_response_data[4]['item'] == 'Bread (500g)'
        assert get_response_data[4]['price'] == 3.78
        assert get_response_data[4]['location']['id'] == 1
        assert get_response_data[4]['location']['country'] == 'Australia'
        assert get_response_data[4]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_country_city_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_response = client.get('/v1/foodbeverage?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 5
        assert get_response_data[0]['item_category'] == 'Beverage'
        assert get_response_data[0]['purchase_point'] == 'Restaurant'
        assert get_response_data[0]['item'] == 'Cappuccino (Regular)'
        assert get_response_data[0]['price'] == 3.64
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['item_category'] == 'Beverage'
        assert get_response_data[1]['purchase_point'] == 'Restaurant'
        assert get_response_data[1]['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data[1]['price'] == 7.41
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['item_category'] == 'Beverage'
        assert get_response_data[2]['purchase_point'] == 'Supermarket'
        assert get_response_data[2]['item'] == 'Milk (1L)'
        assert get_response_data[2]['price'] == 1.82
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['item_category'] == 'Food'
        assert get_response_data[3]['purchase_point'] == 'Restaurant'
        assert get_response_data[3]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_response_data[3]['price'] == 96.31
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response_data[4]['item_category'] == 'Food'
        assert get_response_data[4]['purchase_point'] == 'Supermarket'
        assert get_response_data[4]['item'] == 'Bread (500g)'
        assert get_response_data[4]['price'] == 2.44
        assert get_response_data[4]['location']['id'] == 1
        assert get_response_data[4]['location']['country'] == 'Australia'
        assert get_response_data[4]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_country_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/foodbeverage?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['food and beverage data']) == 5
        assert get_first_page_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][0]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][0]['item'] == 'Cappuccino (Regular)'
        assert get_first_page_response_data['food and beverage data'][0]['price'] == 3.64
        assert get_first_page_response_data['food and beverage data'][0]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][1]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][1]['item'] == 'Domestic Draught (0.5L)'
        assert get_first_page_response_data['food and beverage data'][1]['price'] == 7.41
        assert get_first_page_response_data['food and beverage data'][1]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][2]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][2]['item'] == 'Milk (1L)'
        assert get_first_page_response_data['food and beverage data'][2]['price'] == 1.82
        assert get_first_page_response_data['food and beverage data'][2]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][3]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][3]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][3]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_first_page_response_data['food and beverage data'][3]['price'] == 96.31
        assert get_first_page_response_data['food and beverage data'][3]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][4]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][4]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][4]['item'] == 'Bread (500g)'
        assert get_first_page_response_data['food and beverage data'][4]['price'] == 2.44
        assert get_first_page_response_data['food and beverage data'][4]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][4]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][4]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 5
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

    def test_foodbeverage_get_country_abbreviation_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/foodbeverage?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['food and beverage data']) == 5
        assert get_first_page_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][0]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][0]['item'] == 'Cappuccino (Regular)'
        assert get_first_page_response_data['food and beverage data'][0]['price'] == 5.64
        assert get_first_page_response_data['food and beverage data'][0]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][1]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][1]['item'] == 'Domestic Draught (0.5L)'
        assert get_first_page_response_data['food and beverage data'][1]['price'] == 11.49
        assert get_first_page_response_data['food and beverage data'][1]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][2]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][2]['item'] == 'Milk (1L)'
        assert get_first_page_response_data['food and beverage data'][2]['price'] == 2.82
        assert get_first_page_response_data['food and beverage data'][2]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][3]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][3]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][3]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_first_page_response_data['food and beverage data'][3]['price'] == 149.28
        assert get_first_page_response_data['food and beverage data'][3]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][4]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][4]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][4]['item'] == 'Bread (500g)'
        assert get_first_page_response_data['food and beverage data'][4]['price'] == 3.78
        assert get_first_page_response_data['food and beverage data'][4]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][4]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][4]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 5
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

    def test_foodbeverage_get_city_abbreviation_country_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_response = client.get('/v1/foodbeverage?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 5
        assert get_response_data[0]['item_category'] == 'Beverage'
        assert get_response_data[0]['purchase_point'] == 'Restaurant'
        assert get_response_data[0]['item'] == 'Cappuccino (Regular)'
        assert get_response_data[0]['price'] == 5.64
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['item_category'] == 'Beverage'
        assert get_response_data[1]['purchase_point'] == 'Restaurant'
        assert get_response_data[1]['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data[1]['price'] == 11.49
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['item_category'] == 'Beverage'
        assert get_response_data[2]['purchase_point'] == 'Supermarket'
        assert get_response_data[2]['item'] == 'Milk (1L)'
        assert get_response_data[2]['price'] == 2.82
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['item_category'] == 'Food'
        assert get_response_data[3]['purchase_point'] == 'Restaurant'
        assert get_response_data[3]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_response_data[3]['price'] == 149.28
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response_data[4]['item_category'] == 'Food'
        assert get_response_data[4]['purchase_point'] == 'Supermarket'
        assert get_response_data[4]['item'] == 'Bread (500g)'
        assert get_response_data[4]['price'] == 3.78
        assert get_response_data[4]['location']['id'] == 1
        assert get_response_data[4]['location']['country'] == 'Australia'
        assert get_response_data[4]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_country_none_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/foodbeverage',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['food and beverage data']) == 10
        assert get_first_page_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][0]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][0]['item'] == 'Cappuccino (Regular)'
        assert get_first_page_response_data['food and beverage data'][0]['price'] == 3.64
        assert get_first_page_response_data['food and beverage data'][0]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][1]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][1]['item'] == 'Cappuccino (Regular)'
        assert get_first_page_response_data['food and beverage data'][1]['price'] == 5.05
        assert get_first_page_response_data['food and beverage data'][1]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][2]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][2]['item'] == 'Domestic Draught (0.5L)'
        assert get_first_page_response_data['food and beverage data'][2]['price'] == 6.39
        assert get_first_page_response_data['food and beverage data'][2]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][2]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][2]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][3]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][3]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][3]['item'] == 'Domestic Draught (0.5L)'
        assert get_first_page_response_data['food and beverage data'][3]['price'] == 7.41
        assert get_first_page_response_data['food and beverage data'][3]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][4]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][4]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][4]['item'] == 'Milk (1L)'
        assert get_first_page_response_data['food and beverage data'][4]['price'] == 1.82
        assert get_first_page_response_data['food and beverage data'][4]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][4]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][4]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][5]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][5]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][5]['item'] == 'Milk (1L)'
        assert get_first_page_response_data['food and beverage data'][5]['price'] == 3.08
        assert get_first_page_response_data['food and beverage data'][5]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][5]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][5]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][6]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][6]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][6]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_first_page_response_data['food and beverage data'][6]['price'] == 63.9
        assert get_first_page_response_data['food and beverage data'][6]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][6]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][6]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][7]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][7]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][7]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_first_page_response_data['food and beverage data'][7]['price'] == 96.31
        assert get_first_page_response_data['food and beverage data'][7]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][7]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][7]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][8]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][8]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][8]['item'] == 'Bread (500g)'
        assert get_first_page_response_data['food and beverage data'][8]['price'] == 2.26
        assert get_first_page_response_data['food and beverage data'][8]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][8]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][8]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][9]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][9]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][9]['item'] == 'Bread (500g)'
        assert get_first_page_response_data['food and beverage data'][9]['price'] == 2.44
        assert get_first_page_response_data['food and beverage data'][9]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][9]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][9]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 10
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

    def test_foodbeverage_get_city_country_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_response = client.get('/v1/foodbeverage?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 5
        assert get_response_data[0]['item_category'] == 'Beverage'
        assert get_response_data[0]['purchase_point'] == 'Restaurant'
        assert get_response_data[0]['item'] == 'Cappuccino (Regular)'
        assert get_response_data[0]['price'] == 3.64
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['item_category'] == 'Beverage'
        assert get_response_data[1]['purchase_point'] == 'Restaurant'
        assert get_response_data[1]['item'] == 'Domestic Draught (0.5L)'
        assert get_response_data[1]['price'] == 7.41
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['item_category'] == 'Beverage'
        assert get_response_data[2]['purchase_point'] == 'Supermarket'
        assert get_response_data[2]['item'] == 'Milk (1L)'
        assert get_response_data[2]['price'] == 1.82
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['item_category'] == 'Food'
        assert get_response_data[3]['purchase_point'] == 'Restaurant'
        assert get_response_data[3]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_response_data[3]['price'] == 96.31
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response_data[4]['item_category'] == 'Food'
        assert get_response_data[4]['purchase_point'] == 'Supermarket'
        assert get_response_data[4]['item'] == 'Bread (500g)'
        assert get_response_data[4]['price'] == 2.44
        assert get_response_data[4]['location']['id'] == 1
        assert get_response_data[4]['location']['country'] == 'Australia'
        assert get_response_data[4]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_foodbeverage_get_abbreviation_country_none_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_foodbeverage(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/foodbeverage?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['food and beverage data']) == 10
        print(get_first_page_response_data)
        assert get_first_page_response_data['food and beverage data'][0]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][0]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][0]['item'] == 'Cappuccino (Regular)'
        assert get_first_page_response_data['food and beverage data'][0]['price'] == 5.64
        assert get_first_page_response_data['food and beverage data'][0]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][1]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][1]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][1]['item'] == 'Cappuccino (Regular)'
        assert get_first_page_response_data['food and beverage data'][1]['price'] == 7.83
        assert get_first_page_response_data['food and beverage data'][1]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][1]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][1]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][2]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][2]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][2]['item'] == 'Domestic Draught (0.5L)'
        assert get_first_page_response_data['food and beverage data'][2]['price'] == 9.9
        assert get_first_page_response_data['food and beverage data'][2]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][2]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][2]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][3]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][3]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][3]['item'] == 'Domestic Draught (0.5L)'
        assert get_first_page_response_data['food and beverage data'][3]['price'] == 11.49
        assert get_first_page_response_data['food and beverage data'][3]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][4]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][4]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][4]['item'] == 'Milk (1L)'
        assert get_first_page_response_data['food and beverage data'][4]['price'] == 2.82
        assert get_first_page_response_data['food and beverage data'][4]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][4]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][4]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][5]['item_category'] == 'Beverage'
        assert get_first_page_response_data['food and beverage data'][5]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][5]['item'] == 'Milk (1L)'
        assert get_first_page_response_data['food and beverage data'][5]['price'] == 4.77
        assert get_first_page_response_data['food and beverage data'][5]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][5]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][5]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][6]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][6]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][6]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_first_page_response_data['food and beverage data'][6]['price'] == 99.05
        assert get_first_page_response_data['food and beverage data'][6]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][6]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][6]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][7]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][7]['purchase_point'] == 'Restaurant'
        assert get_first_page_response_data['food and beverage data'][7]['item'] == 'Dinner (2 People Mid Range Restaurant)'
        assert get_first_page_response_data['food and beverage data'][7]['price'] == 149.28
        assert get_first_page_response_data['food and beverage data'][7]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][7]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][7]['location']['city'] == 'Perth'
        assert get_first_page_response_data['food and beverage data'][8]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][8]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][8]['item'] == 'Bread (500g)'
        assert get_first_page_response_data['food and beverage data'][8]['price'] == 3.5
        assert get_first_page_response_data['food and beverage data'][8]['location']['id'] == 2
        assert get_first_page_response_data['food and beverage data'][8]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][8]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['food and beverage data'][9]['item_category'] == 'Food'
        assert get_first_page_response_data['food and beverage data'][9]['purchase_point'] == 'Supermarket'
        assert get_first_page_response_data['food and beverage data'][9]['item'] == 'Bread (500g)'
        assert get_first_page_response_data['food and beverage data'][9]['price'] == 3.78
        assert get_first_page_response_data['food and beverage data'][9]['location']['id'] == 1
        assert get_first_page_response_data['food and beverage data'][9]['location']['country'] == 'Australia'
        assert get_first_page_response_data['food and beverage data'][9]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 10
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
    def test_childcare_get_with_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_response = client.get('/v1/childcare/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['type'] == 'Daycare / Preschool (1 Year)'
        assert get_response_data['annual_price'] == 19411.68
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_response = client.get('/v1/childcare/5',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_childcare_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        delete_response = client.delete('/v1/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Childcare id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Childcare.query.count() == 3

    def test_childcare_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Childcare.query.count() == 0
    
    def test_childcare_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        delete_response = client.delete('/v1/childcare/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestChildcareListResource:
    def test_childcare_post_childcare_location_notexist(self,client, mock_environment_variables, mock_boto3_s3):
        response = create_childcare(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Childcare.query.count() == 0
    
    def test_childcare_post_childcare_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = client.post('/v1/childcare',
        headers = {'Content-Type': 'application/json'})
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.bad_request_400.value
        assert post_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
        assert Childcare.query.count() == 0
    
    def test_childcare_post_childcare_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/childcare',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert Childcare.query.count() == 0

    def test_childcare_post_childcare_with_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = create_childcare(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == f'Successfully added 4 childcare records'
        assert Childcare.query.count() == 4
    
    def test_childcare_patch_updated_data(self,client,create_user,login, mock_environment_variables, mock_boto3_s3_patch_modified):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        patch_response = childcare_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 2 childcare records'
        get_response = client.get('/v1/childcare',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response.status_code == HttpStatus.ok_200.value
        assert len(get_response_data['childcare data']) == 4
        assert get_response_data['childcare data'][0]['type'] == 'Daycare / Preschool'
        assert get_response_data['childcare data'][0]['annual_price'] == 9404.64
        assert get_response_data['childcare data'][0]['location']['id'] == 2
        assert get_response_data['childcare data'][0]['location']['country'] == 'Hong Kong'
        assert get_response_data['childcare data'][0]['location']['city'] == 'Hong Kong'
        assert get_response_data['childcare data'][1]['type'] == 'Daycare / Preschool'
        assert get_response_data['childcare data'][1]['annual_price'] == 20599.08
        assert get_response_data['childcare data'][1]['location']['id'] == 1
        assert get_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_response_data['childcare data'][1]['location']['city'] == 'Perth'
        assert get_response_data['childcare data'][2]['type'] == 'International Primary School'
        assert get_response_data['childcare data'][2]['annual_price'] == 13837.01
        assert get_response_data['childcare data'][2]['location']['id'] == 1
        assert get_response_data['childcare data'][2]['location']['country'] == 'Australia'
        assert get_response_data['childcare data'][2]['location']['city'] == 'Perth'
        assert get_response_data['childcare data'][3]['type'] == 'International Primary School'
        assert get_response_data['childcare data'][3]['annual_price'] == 20470.76
        assert get_response_data['childcare data'][3]['location']['id'] == 2
        assert get_response_data['childcare data'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['childcare data'][3]['location']['city'] == 'Hong Kong'

    def test_childcare_patch_no_updated_data(self,client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        patch_response = childcare_patch_updated_data(client, mock_environment_variables, mock_boto3_s3)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 0 childcare records'
        get_response = client.get('/v1/childcare',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response.status_code == HttpStatus.ok_200.value
        print(get_response_data)
        assert len(get_response_data['childcare data']) == 4
        assert get_response_data['childcare data'][0]['type'] == 'Daycare / Preschool'
        assert get_response_data['childcare data'][0]['annual_price'] == 9404.64
        assert get_response_data['childcare data'][0]['location']['id'] == 2
        assert get_response_data['childcare data'][0]['location']['country'] == 'Hong Kong'
        assert get_response_data['childcare data'][0]['location']['city'] == 'Hong Kong'
        assert get_response_data['childcare data'][1]['type'] == 'Daycare / Preschool'
        assert get_response_data['childcare data'][1]['annual_price'] == 19411.68
        assert get_response_data['childcare data'][1]['location']['id'] == 1
        assert get_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_response_data['childcare data'][1]['location']['city'] == 'Perth'
        assert get_response_data['childcare data'][2]['type'] == 'International Primary School'
        assert get_response_data['childcare data'][2]['annual_price'] == 13498.21
        assert get_response_data['childcare data'][2]['location']['id'] == 1
        assert get_response_data['childcare data'][2]['location']['country'] == 'Australia'
        assert get_response_data['childcare data'][2]['location']['city'] == 'Perth'
        assert get_response_data['childcare data'][3]['type'] == 'International Primary School'
        assert get_response_data['childcare data'][3]['annual_price'] == 20470.76
        assert get_response_data['childcare data'][3]['location']['id'] == 2
        assert get_response_data['childcare data'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['childcare data'][3]['location']['city'] == 'Hong Kong'
    
    def test_childcare_patch_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        patch_response = client.patch('/v1/childcare',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_childcare_patch_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        response = client.patch('/v1/childcare',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_childcare_get_country_city_abbreviation(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_response = client.get('/v1/childcare?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 2
        assert get_response_data[0]['type'] == 'Daycare / Preschool'
        assert get_response_data[0]['annual_price'] == 30088.1
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['type'] == 'International Primary School'
        assert get_response_data[1]['annual_price'] == 20922.23
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_country_city_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_response = client.get('/v1/childcare?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 2
        assert get_response_data[0]['type'] == 'Daycare / Preschool'
        assert get_response_data[0]['annual_price'] == 19411.68
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['type'] == 'International Primary School'
        assert get_response_data[1]['annual_price'] == 13498.21
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_country_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/childcare?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['childcare data']) == 2
        assert get_first_page_response_data['childcare data'][0]['type'] == 'Daycare / Preschool'
        assert get_first_page_response_data['childcare data'][0]['annual_price'] == 19411.68
        assert get_first_page_response_data['childcare data'][0]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][1]['type'] == 'International Primary School'
        assert get_first_page_response_data['childcare data'][1]['annual_price'] == 13498.21
        assert get_first_page_response_data['childcare data'][1]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 2
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

    def test_childcare_get_country_abbreviation_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/childcare?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['childcare data']) == 2
        assert get_first_page_response_data['childcare data'][0]['type'] == 'Daycare / Preschool'
        assert get_first_page_response_data['childcare data'][0]['annual_price'] == 30088.1
        assert get_first_page_response_data['childcare data'][0]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][1]['type'] == 'International Primary School'
        assert get_first_page_response_data['childcare data'][1]['annual_price'] == 20922.23
        assert get_first_page_response_data['childcare data'][1]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 2
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

    def test_childcare_get_city_abbreviation_country_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_response = client.get('/v1/childcare?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 2
        assert get_response_data[0]['type'] == 'Daycare / Preschool'
        assert get_response_data[0]['annual_price'] == 30088.1
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['type'] == 'International Primary School'
        assert get_response_data[1]['annual_price'] == 20922.23
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_country_none_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/childcare',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['childcare data']) == 4
        assert get_first_page_response_data['childcare data'][0]['type'] == 'Daycare / Preschool'
        assert get_first_page_response_data['childcare data'][0]['annual_price'] == 9404.64
        assert get_first_page_response_data['childcare data'][0]['location']['id'] == 2
        assert get_first_page_response_data['childcare data'][0]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['childcare data'][0]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['childcare data'][1]['type'] == 'Daycare / Preschool'
        assert get_first_page_response_data['childcare data'][1]['annual_price'] == 19411.68
        assert get_first_page_response_data['childcare data'][1]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][2]['type'] == 'International Primary School'
        assert get_first_page_response_data['childcare data'][2]['annual_price'] == 13498.21
        assert get_first_page_response_data['childcare data'][2]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][3]['type'] == 'International Primary School'
        assert get_first_page_response_data['childcare data'][3]['annual_price'] == 20470.76
        assert get_first_page_response_data['childcare data'][3]['location']['id'] == 2
        assert get_first_page_response_data['childcare data'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['childcare data'][3]['location']['city'] == 'Hong Kong'
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

    def test_childcare_get_city_country_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_response = client.get('/v1/childcare?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 2
        assert get_response_data[0]['type'] == 'Daycare / Preschool'
        assert get_response_data[0]['annual_price'] == 19411.68
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['type'] == 'International Primary School'
        assert get_response_data[1]['annual_price'] == 13498.21
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_childcare_get_abbreviation_country_none_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_childcare(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/childcare?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['childcare data']) == 4
        assert get_first_page_response_data['childcare data'][0]['type'] == 'Daycare / Preschool'
        assert get_first_page_response_data['childcare data'][0]['annual_price'] == 14577.19
        assert get_first_page_response_data['childcare data'][0]['location']['id'] == 2
        assert get_first_page_response_data['childcare data'][0]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['childcare data'][0]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['childcare data'][1]['type'] == 'Daycare / Preschool'
        assert get_first_page_response_data['childcare data'][1]['annual_price'] == 30088.1
        assert get_first_page_response_data['childcare data'][1]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][2]['type'] == 'International Primary School'
        assert get_first_page_response_data['childcare data'][2]['annual_price'] == 20922.23
        assert get_first_page_response_data['childcare data'][2]['location']['id'] == 1
        assert get_first_page_response_data['childcare data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['childcare data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['childcare data'][3]['type'] == 'International Primary School'
        assert get_first_page_response_data['childcare data'][3]['annual_price'] == 31729.68
        assert get_first_page_response_data['childcare data'][3]['location']['id'] == 2
        assert get_first_page_response_data['childcare data'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['childcare data'][3]['location']['city'] == 'Hong Kong'
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
    def test_apparel_get_with_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_response = client.get('/v1/apparel/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['item'] == 'Pair of Jeans'
        assert get_response_data['price'] == 87.19
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_response = client.get('/v1/apparel/10',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_apparel_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        delete_response = client.delete('/v1/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Apparel id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Apparel.query.count() == 7

    def test_apparel_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Apparel.query.count() == 0
    
    def test_apparel_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        delete_response = client.delete('/v1/apparel/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestApparelListResource:
    def test_apparel_post_apparel_location_notexist(self,client, mock_environment_variables, mock_boto3_s3):
        response = create_apparel(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Apparel.query.count() == 0
    
    def test_apparel_post_apparel_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = client.post('/v1/apparel')
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.bad_request_400.value
        assert post_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
        assert Apparel.query.count() == 0
    
    def test_apparel_post_apparel_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/apparel',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert Apparel.query.count() == 0

    def test_apparel_post_apparel_with_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = create_apparel(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == f'Successfully added 8 apparel records'
        assert Apparel.query.count() == 8
    
    def test_apparel_patch_updated_data(self,client,create_user,login, mock_environment_variables, mock_boto3_s3_patch_modified):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        patch_response = apparel_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 4 apparel records'
        get_response = client.get('/v1/apparel',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['apparel data']) == 8
        assert get_response_data['apparel data'][0]['item'] == 'Brand Sneakers'
        assert get_response_data['apparel data'][0]['price'] == 86.5
        assert get_response_data['apparel data'][0]['location']['id'] == 2
        assert get_response_data['apparel data'][0]['location']['country'] == 'Hong Kong'
        assert get_response_data['apparel data'][0]['location']['city'] == 'Hong Kong'
        assert get_response_data['apparel data'][1]['item'] == 'Brand Sneakers'
        assert get_response_data['apparel data'][1]['price'] == 139.1
        assert get_response_data['apparel data'][1]['location']['id'] == 1
        assert get_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_response_data['apparel data'][1]['location']['city'] == 'Perth'
        assert get_response_data['apparel data'][2]['item'] == 'Mens Leather Business Shoes'
        assert get_response_data['apparel data'][2]['price'] == 127.96
        assert get_response_data['apparel data'][2]['location']['id'] == 2
        assert get_response_data['apparel data'][2]['location']['country'] == 'Hong Kong'
        assert get_response_data['apparel data'][2]['location']['city'] == 'Hong Kong'
        assert get_response_data['apparel data'][3]['item'] == 'Mens Leather Business Shoes'
        assert get_response_data['apparel data'][3]['price'] == 171.78
        assert get_response_data['apparel data'][3]['location']['id'] == 1
        assert get_response_data['apparel data'][3]['location']['country'] == 'Australia'
        assert get_response_data['apparel data'][3]['location']['city'] == 'Perth'
        assert get_response_data['apparel data'][4]['item'] == 'Pair of Jeans'
        assert get_response_data['apparel data'][4]['price'] == 81.83
        assert get_response_data['apparel data'][4]['location']['id'] == 2
        assert get_response_data['apparel data'][4]['location']['country'] == 'Hong Kong'
        assert get_response_data['apparel data'][4]['location']['city'] == 'Hong Kong'
        assert get_response_data['apparel data'][5]['item'] == 'Pair of Jeans'
        assert get_response_data['apparel data'][5]['price'] == 90.22
        assert get_response_data['apparel data'][5]['location']['id'] == 1
        assert get_response_data['apparel data'][5]['location']['country'] == 'Australia'
        assert get_response_data['apparel data'][5]['location']['city'] == 'Perth'
        assert get_response_data['apparel data'][6]['item'] == 'Summer Dress Chain Store'
        assert get_response_data['apparel data'][6]['price'] == 41.51
        assert get_response_data['apparel data'][6]['location']['id'] == 2
        assert get_response_data['apparel data'][6]['location']['country'] == 'Hong Kong'
        assert get_response_data['apparel data'][6]['location']['city'] == 'Hong Kong'
        assert get_response_data['apparel data'][7]['item'] == 'Summer Dress Chain Store'
        assert get_response_data['apparel data'][7]['price'] == 74.84
        assert get_response_data['apparel data'][7]['location']['id'] == 1
        assert get_response_data['apparel data'][7]['location']['country'] == 'Australia'
        assert get_response_data['apparel data'][7]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value
    
    def test_apparel_patch_no_updated_data(self, client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        patch_response = apparel_patch_updated_data(client, mock_environment_variables, mock_boto3_s3)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.ok_200.value
        assert patch_response_data['message'] == 'Successfully updated 0 apparel records'
        get_response = client.get('/v1/apparel',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['apparel data']) == 8
        assert get_response_data['apparel data'][0]['item'] == 'Brand Sneakers'
        assert get_response_data['apparel data'][0]['price'] == 86.5
        assert get_response_data['apparel data'][0]['location']['id'] == 2
        assert get_response_data['apparel data'][0]['location']['country'] == 'Hong Kong'
        assert get_response_data['apparel data'][0]['location']['city'] == 'Hong Kong'
        assert get_response_data['apparel data'][1]['item'] == 'Brand Sneakers'
        assert get_response_data['apparel data'][1]['price'] == 139.0
        assert get_response_data['apparel data'][1]['location']['id'] == 1
        assert get_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_response_data['apparel data'][1]['location']['city'] == 'Perth'
        assert get_response_data['apparel data'][2]['item'] == 'Mens Leather Business Shoes'
        assert get_response_data['apparel data'][2]['price'] == 127.96
        assert get_response_data['apparel data'][2]['location']['id'] == 2
        assert get_response_data['apparel data'][2]['location']['country'] == 'Hong Kong'
        assert get_response_data['apparel data'][2]['location']['city'] == 'Hong Kong'
        assert get_response_data['apparel data'][3]['item'] == 'Mens Leather Business Shoes'
        assert get_response_data['apparel data'][3]['price'] == 161.79
        assert get_response_data['apparel data'][3]['location']['id'] == 1
        assert get_response_data['apparel data'][3]['location']['country'] == 'Australia'
        assert get_response_data['apparel data'][3]['location']['city'] == 'Perth'
        assert get_response_data['apparel data'][4]['item'] == 'Pair of Jeans'
        assert get_response_data['apparel data'][4]['price'] == 81.83
        assert get_response_data['apparel data'][4]['location']['id'] == 2
        assert get_response_data['apparel data'][4]['location']['country'] == 'Hong Kong'
        assert get_response_data['apparel data'][4]['location']['city'] == 'Hong Kong'
        assert get_response_data['apparel data'][5]['item'] == 'Pair of Jeans'
        assert get_response_data['apparel data'][5]['price'] == 87.19
        assert get_response_data['apparel data'][5]['location']['id'] == 1
        assert get_response_data['apparel data'][5]['location']['country'] == 'Australia'
        assert get_response_data['apparel data'][5]['location']['city'] == 'Perth'
        assert get_response_data['apparel data'][6]['item'] == 'Summer Dress Chain Store'
        assert get_response_data['apparel data'][6]['price'] == 41.51
        assert get_response_data['apparel data'][6]['location']['id'] == 2
        assert get_response_data['apparel data'][6]['location']['country'] == 'Hong Kong'
        assert get_response_data['apparel data'][6]['location']['city'] == 'Hong Kong'
        assert get_response_data['apparel data'][7]['item'] == 'Summer Dress Chain Store'
        assert get_response_data['apparel data'][7]['price'] == 62.76
        assert get_response_data['apparel data'][7]['location']['id'] == 1
        assert get_response_data['apparel data'][7]['location']['country'] == 'Australia'
        assert get_response_data['apparel data'][7]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_patch_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        patch_response = client.patch('/v1/apparel',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_apparel_update_incorrect_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        response = client.patch('/v1/apparel',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_apparel_get_country_city_abbreviation(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_response = client.get('/v1/apparel?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item'] == 'Brand Sneakers'
        assert get_response_data[0]['price'] == 215.45
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['item'] == 'Mens Leather Business Shoes'
        assert get_response_data[1]['price'] == 250.77
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['item'] == 'Pair of Jeans'
        assert get_response_data[2]['price'] == 135.14
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['item'] == 'Summer Dress Chain Store'
        assert get_response_data[3]['price'] == 97.28
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_country_city_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_response = client.get('/v1/apparel?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item'] == 'Brand Sneakers'
        assert get_response_data[0]['price'] == 139.0
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['item'] == 'Mens Leather Business Shoes'
        assert get_response_data[1]['price'] == 161.79
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['item'] == 'Pair of Jeans'
        assert get_response_data[2]['price'] == 87.19
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['item'] == 'Summer Dress Chain Store'
        assert get_response_data[3]['price'] == 62.76
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_country_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/apparel?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['apparel data']) == 4
        assert get_first_page_response_data['apparel data'][0]['item'] == 'Brand Sneakers'
        assert get_first_page_response_data['apparel data'][0]['price'] == 139.0
        assert get_first_page_response_data['apparel data'][0]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][1]['item'] == 'Mens Leather Business Shoes'
        assert get_first_page_response_data['apparel data'][1]['price'] == 161.79
        assert get_first_page_response_data['apparel data'][1]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][2]['item'] == 'Pair of Jeans'
        assert get_first_page_response_data['apparel data'][2]['price'] == 87.19
        assert get_first_page_response_data['apparel data'][2]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][3]['item'] == 'Summer Dress Chain Store'
        assert get_first_page_response_data['apparel data'][3]['price'] == 62.76
        assert get_first_page_response_data['apparel data'][3]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 4
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

    def test_apparel_get_country_abbreviation_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/apparel?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['apparel data']) == 4
        assert get_first_page_response_data['apparel data'][0]['item'] == 'Brand Sneakers'
        assert get_first_page_response_data['apparel data'][0]['price'] == 215.45
        assert get_first_page_response_data['apparel data'][0]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][1]['item'] == 'Mens Leather Business Shoes'
        assert get_first_page_response_data['apparel data'][1]['price'] == 250.77
        assert get_first_page_response_data['apparel data'][1]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][2]['item'] == 'Pair of Jeans'
        assert get_first_page_response_data['apparel data'][2]['price'] == 135.14
        assert get_first_page_response_data['apparel data'][2]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][3]['item'] == 'Summer Dress Chain Store'
        assert get_first_page_response_data['apparel data'][3]['price'] == 97.28
        assert get_first_page_response_data['apparel data'][3]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 4
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

    def test_apparel_get_city_abbreviation_country_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_response = client.get('/v1/apparel?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item'] == 'Brand Sneakers'
        assert get_response_data[0]['price'] == 215.45
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['item'] == 'Mens Leather Business Shoes'
        assert get_response_data[1]['price'] == 250.77
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['item'] == 'Pair of Jeans'
        assert get_response_data[2]['price'] == 135.14
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['item'] == 'Summer Dress Chain Store'
        assert get_response_data[3]['price'] == 97.28
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_country_none_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/apparel',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['apparel data']) == 8
        assert get_first_page_response_data['apparel data'][0]['item'] == 'Brand Sneakers'
        assert get_first_page_response_data['apparel data'][0]['price'] == 86.5
        assert get_first_page_response_data['apparel data'][0]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][0]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][0]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][1]['item'] == 'Brand Sneakers'
        assert get_first_page_response_data['apparel data'][1]['price'] == 139.0
        assert get_first_page_response_data['apparel data'][1]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][2]['item'] == 'Mens Leather Business Shoes'
        assert get_first_page_response_data['apparel data'][2]['price'] == 127.96
        assert get_first_page_response_data['apparel data'][2]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][2]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][2]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][3]['item'] == 'Mens Leather Business Shoes'
        assert get_first_page_response_data['apparel data'][3]['price'] == 161.79
        assert get_first_page_response_data['apparel data'][3]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][4]['item'] == 'Pair of Jeans'
        assert get_first_page_response_data['apparel data'][4]['price'] == 81.83
        assert get_first_page_response_data['apparel data'][4]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][4]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][4]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][5]['item'] == 'Pair of Jeans'
        assert get_first_page_response_data['apparel data'][5]['price'] == 87.19
        assert get_first_page_response_data['apparel data'][5]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][5]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][5]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][6]['item'] == 'Summer Dress Chain Store'
        assert get_first_page_response_data['apparel data'][6]['price'] == 41.51
        assert get_first_page_response_data['apparel data'][6]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][6]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][6]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][7]['item'] == 'Summer Dress Chain Store'
        assert get_first_page_response_data['apparel data'][7]['price'] == 62.76
        assert get_first_page_response_data['apparel data'][7]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][7]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][7]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 8
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

    def test_apparel_get_city_country_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_response = client.get('/v1/apparel?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data[0]['item'] == 'Brand Sneakers'
        assert get_response_data[0]['price'] == 139.0
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['item'] == 'Mens Leather Business Shoes'
        assert get_response_data[1]['price'] == 161.79
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['item'] == 'Pair of Jeans'
        assert get_response_data[2]['price'] == 87.19
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response_data[3]['item'] == 'Summer Dress Chain Store'
        assert get_response_data[3]['price'] == 62.76
        assert get_response_data[3]['location']['id'] == 1
        assert get_response_data[3]['location']['country'] == 'Australia'
        assert get_response_data[3]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_apparel_get_abbreviation_country_none_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_apparel(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/apparel?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['apparel data']) == 8
        assert get_first_page_response_data['apparel data'][0]['item'] == 'Brand Sneakers'
        assert get_first_page_response_data['apparel data'][0]['price'] == 134.08
        assert get_first_page_response_data['apparel data'][0]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][0]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][0]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][1]['item'] == 'Brand Sneakers'
        assert get_first_page_response_data['apparel data'][1]['price'] == 215.45
        assert get_first_page_response_data['apparel data'][1]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][2]['item'] == 'Mens Leather Business Shoes'
        assert get_first_page_response_data['apparel data'][2]['price'] == 198.34
        assert get_first_page_response_data['apparel data'][2]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][2]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][2]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][3]['item'] == 'Mens Leather Business Shoes'
        assert get_first_page_response_data['apparel data'][3]['price'] == 250.77
        assert get_first_page_response_data['apparel data'][3]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][3]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][3]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][4]['item'] == 'Pair of Jeans'
        assert get_first_page_response_data['apparel data'][4]['price'] == 126.84
        assert get_first_page_response_data['apparel data'][4]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][4]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][4]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][5]['item'] == 'Pair of Jeans'
        assert get_first_page_response_data['apparel data'][5]['price'] == 135.14
        assert get_first_page_response_data['apparel data'][5]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][5]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][5]['location']['city'] == 'Perth'
        assert get_first_page_response_data['apparel data'][6]['item'] == 'Summer Dress Chain Store'
        assert get_first_page_response_data['apparel data'][6]['price'] == 64.34
        assert get_first_page_response_data['apparel data'][6]['location']['id'] == 2
        assert get_first_page_response_data['apparel data'][6]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][6]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['apparel data'][7]['item'] == 'Summer Dress Chain Store'
        assert get_first_page_response_data['apparel data'][7]['price'] == 97.28
        assert get_first_page_response_data['apparel data'][7]['location']['id'] == 1
        assert get_first_page_response_data['apparel data'][7]['location']['country'] == 'Australia'
        assert get_first_page_response_data['apparel data'][7]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 8
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

class TestLeisureResource:
    def test_leisure_get_with_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_response = client.get('/v1/leisure/1',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert get_response_data['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data['price'] == 49.05
        assert get_response_data['location']['id'] == 1
        assert get_response_data['location']['country'] == 'Australia'
        assert get_response_data['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_notexist_id(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_response = client.get('/v1/leisure/7',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        assert get_response.status_code == HttpStatus.notfound_404.value

    def test_leisure_delete(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        delete_response = client.delete('/v1/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response_data['message'] == 'Leisure id successfully deleted'
        assert delete_response.status_code == HttpStatus.ok_200.value
        assert Leisure.query.count() == 5

    def test_leisure_delete_no_id_exist(self,client):
        delete_response = client.delete('/v1/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': os.environ.get('ADMIN_KEY')}))
        assert delete_response.status_code == HttpStatus.notfound_404.value
        assert Leisure.query.count() == 0
    
    def test_leisure_delete_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        delete_response = client.delete('/v1/leisure/1',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({}))
        delete_response_data = json.loads(delete_response.get_data(as_text = True))
        assert delete_response.status_code == HttpStatus.forbidden_403.value
        assert delete_response_data['message'] == 'Admin privileges needed'

class TestLeisureListResource:
    def test_leisure_post_leisure_location_notexist(self,client, mock_environment_variables, mock_boto3_s3):
        response = create_leisure(client, mock_environment_variables)
        response_data = json.loads(response.get_data(as_text = True))
        assert response_data['message'] == 'Specified city doesnt exist in /locations/ API endpoint'
        assert response.status_code == HttpStatus.notfound_404.value
        assert Leisure.query.count() == 0
    
    def test_leisure_post_leisure_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/leisure',
        headers = {'Content-Type': 'application/json'})
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.bad_request_400.value
        assert response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
        assert Leisure.query.count() == 0
    
    def test_leisure_post_leisure_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        response = client.post('/v1/leisure',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert response_data['message'] == 'Admin privileges needed'
        assert Leisure.query.count() == 0

    def test_leisure_post_leisure_with_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        post_response = create_leisure(client, mock_environment_variables)
        post_response_data = json.loads(post_response.get_data(as_text = True))
        assert post_response.status_code == HttpStatus.created_201.value
        assert post_response_data['message'] == f'Successfully added 6 leisure records'
        assert Leisure.query.count() == 6
    
    def test_leisure_patch_updated_data(self,client,create_user,login, mock_environment_variables, mock_boto3_s3_patch_modified):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        patch_response = leisure_patch_updated_data(client, mock_environment_variables, mock_boto3_s3_patch_modified)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response_data['message'] == 'Successfully updated 3 leisure records'
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/leisure',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['leisure data']) == 6
        assert get_response_data['leisure data'][0]['activity'] == 'Cinema International Release'
        assert get_response_data['leisure data'][0]['price'] == 12.78
        assert get_response_data['leisure data'][0]['location']['id'] == 2
        assert get_response_data['leisure data'][0]['location']['country'] == 'Hong Kong'
        assert get_response_data['leisure data'][0]['location']['city'] == 'Hong Kong'
        assert get_response_data['leisure data'][1]['activity'] == 'Cinema International Release'
        assert get_response_data['leisure data'][1]['price'] == 15.3
        assert get_response_data['leisure data'][1]['location']['id'] == 1
        assert get_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_response_data['leisure data'][1]['location']['city'] == 'Perth'
        assert get_response_data['leisure data'][2]['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data['leisure data'][2]['price'] == 49.56
        assert get_response_data['leisure data'][2]['location']['id'] == 1
        assert get_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_response_data['leisure data'][2]['location']['city'] == 'Perth'
        assert get_response_data['leisure data'][3]['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data['leisure data'][3]['price'] == 88.44
        assert get_response_data['leisure data'][3]['location']['id'] == 2
        assert get_response_data['leisure data'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['leisure data'][3]['location']['city'] == 'Hong Kong'
        assert get_response_data['leisure data'][4]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_response_data['leisure data'][4]['price'] == 8.85
        assert get_response_data['leisure data'][4]['location']['id'] == 2
        assert get_response_data['leisure data'][4]['location']['country'] == 'Hong Kong'
        assert get_response_data['leisure data'][4]['location']['city'] == 'Hong Kong'
        assert get_response_data['leisure data'][5]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_response_data['leisure data'][5]['price'] == 15.25
        assert get_response_data['leisure data'][5]['location']['id'] == 1
        assert get_response_data['leisure data'][5]['location']['country'] == 'Australia'
        assert get_response_data['leisure data'][5]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_patch_no_updated_data(self,client, create_user, login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        patch_response = leisure_patch_updated_data(client, mock_environment_variables, mock_boto3_s3)
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response_data['message'] == 'Successfully updated 0 leisure records'
        assert patch_response.status_code == HttpStatus.ok_200.value
        get_response = client.get('/v1/leisure',
            headers = {'Content-Type': 'application/json',
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data['leisure data']) == 6
        assert get_response_data['leisure data'][0]['activity'] == 'Cinema International Release'
        assert get_response_data['leisure data'][0]['price'] == 12.78
        assert get_response_data['leisure data'][0]['location']['id'] == 2
        assert get_response_data['leisure data'][0]['location']['country'] == 'Hong Kong'
        assert get_response_data['leisure data'][0]['location']['city'] == 'Hong Kong'
        assert get_response_data['leisure data'][1]['activity'] == 'Cinema International Release'
        assert get_response_data['leisure data'][1]['price'] == 14.82
        assert get_response_data['leisure data'][1]['location']['id'] == 1
        assert get_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_response_data['leisure data'][1]['location']['city'] == 'Perth'
        assert get_response_data['leisure data'][2]['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data['leisure data'][2]['price'] == 49.05
        assert get_response_data['leisure data'][2]['location']['id'] == 1
        assert get_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_response_data['leisure data'][2]['location']['city'] == 'Perth'
        assert get_response_data['leisure data'][3]['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data['leisure data'][3]['price'] == 88.44
        assert get_response_data['leisure data'][3]['location']['id'] == 2
        assert get_response_data['leisure data'][3]['location']['country'] == 'Hong Kong'
        assert get_response_data['leisure data'][3]['location']['city'] == 'Hong Kong'
        assert get_response_data['leisure data'][4]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_response_data['leisure data'][4]['price'] == 8.85
        assert get_response_data['leisure data'][4]['location']['id'] == 2
        assert get_response_data['leisure data'][4]['location']['country'] == 'Hong Kong'
        assert get_response_data['leisure data'][4]['location']['city'] == 'Hong Kong'
        assert get_response_data['leisure data'][5]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_response_data['leisure data'][5]['price'] == 14.92
        assert get_response_data['leisure data'][5]['location']['id'] == 1
        assert get_response_data['leisure data'][5]['location']['country'] == 'Australia'
        assert get_response_data['leisure data'][5]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value
    
    def test_leisure_patch_no_admin(self,client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        patch_response = client.patch('/v1/leisure',
        headers = {'Content-Type': 'application/json'})
        patch_response_data = json.loads(patch_response.get_data(as_text = True))
        assert patch_response.status_code == HttpStatus.bad_request_400.value
        assert patch_response_data['message'] == 'The browser (or proxy) sent a request that this server could not understand.'
    
    def test_leisure_patch_incorrect_admin(self, client, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        response = client.patch('/v1/leisure',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'admin': 'incorrectadmin'}))
        patch_response_data = json.loads(response.get_data(as_text = True))
        assert response.status_code == HttpStatus.forbidden_403.value
        assert patch_response_data['message'] == 'Admin privileges needed'

    def test_leisure_get_country_city_abbreviation(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_response = client.get('/v1/leisure?country=Australia&city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 3
        assert get_response_data[0]['activity'] == 'Cinema International Release'
        assert get_response_data[0]['price'] == 22.97
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data[1]['price'] == 76.03
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_response_data[2]['price'] == 23.13
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_country_city_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_response = client.get('/v1/leisure?country=Australia&city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 3
        assert get_response_data[0]['activity'] == 'Cinema International Release'
        assert get_response_data[0]['price'] == 14.82
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data[1]['price'] == 49.05
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_response_data[2]['price'] == 14.92
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_country_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/leisure?country=Australia',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['leisure data']) == 3
        assert get_first_page_response_data['leisure data'][0]['activity'] == 'Cinema International Release'
        assert get_first_page_response_data['leisure data'][0]['price'] == 14.82
        assert get_first_page_response_data['leisure data'][0]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][1]['activity'] == 'Gym Membership (Monthly)'
        assert get_first_page_response_data['leisure data'][1]['price'] == 49.05
        assert get_first_page_response_data['leisure data'][1]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][2]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_first_page_response_data['leisure data'][2]['price'] == 14.92
        assert get_first_page_response_data['leisure data'][2]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][2]['location']['city'] == 'Perth'
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

    def test_leisure_get_country_abbreviation_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/leisure?country=Australia&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['leisure data']) == 3
        assert get_first_page_response_data['leisure data'][0]['activity'] == 'Cinema International Release'
        assert get_first_page_response_data['leisure data'][0]['price'] == 22.97
        assert get_first_page_response_data['leisure data'][0]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][0]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][0]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][1]['activity'] == 'Gym Membership (Monthly)'
        assert get_first_page_response_data['leisure data'][1]['price'] == 76.03
        assert get_first_page_response_data['leisure data'][1]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][2]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_first_page_response_data['leisure data'][2]['price'] == 23.13
        assert get_first_page_response_data['leisure data'][2]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][2]['location']['city'] == 'Perth'
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

    def test_leisure_get_city_abbreviation_country_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_response = client.get('/v1/leisure?city=Perth&abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 3
        assert get_response_data[0]['activity'] == 'Cinema International Release'
        assert get_response_data[0]['price'] == 22.97
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data[1]['price'] == 76.03
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_response_data[2]['price'] == 23.13
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_country_none_city_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/leisure',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['leisure data']) == 6
        assert get_first_page_response_data['leisure data'][0]['activity'] == 'Cinema International Release'
        assert get_first_page_response_data['leisure data'][0]['price'] == 12.78
        assert get_first_page_response_data['leisure data'][0]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][0]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][0]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][1]['activity'] == 'Cinema International Release'
        assert get_first_page_response_data['leisure data'][1]['price'] == 14.82
        assert get_first_page_response_data['leisure data'][1]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][2]['activity'] == 'Gym Membership (Monthly)'
        assert get_first_page_response_data['leisure data'][2]['price'] == 49.05
        assert get_first_page_response_data['leisure data'][2]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][3]['activity'] == 'Gym Membership (Monthly)'
        assert get_first_page_response_data['leisure data'][3]['price'] == 88.44
        assert get_first_page_response_data['leisure data'][3]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][3]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][4]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_first_page_response_data['leisure data'][4]['price'] == 8.85
        assert get_first_page_response_data['leisure data'][4]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][4]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][4]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][5]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_first_page_response_data['leisure data'][5]['price'] == 14.92
        assert get_first_page_response_data['leisure data'][5]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][5]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][5]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 6
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

    def test_leisure_get_city_country_none_abbreviation_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_response = client.get('/v1/leisure?city=Perth',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_response_data = json.loads(get_response.get_data(as_text = True))
        assert len(get_response_data) == 3
        assert get_response_data[0]['activity'] == 'Cinema International Release'
        assert get_response_data[0]['price'] == 14.82
        assert get_response_data[0]['location']['id'] == 1
        assert get_response_data[0]['location']['country'] == 'Australia'
        assert get_response_data[0]['location']['city'] == 'Perth'
        assert get_response_data[1]['activity'] == 'Gym Membership (Monthly)'
        assert get_response_data[1]['price'] == 49.05
        assert get_response_data[1]['location']['id'] == 1
        assert get_response_data[1]['location']['country'] == 'Australia'
        assert get_response_data[1]['location']['city'] == 'Perth'
        assert get_response_data[2]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_response_data[2]['price'] == 14.92
        assert get_response_data[2]['location']['id'] == 1
        assert get_response_data[2]['location']['country'] == 'Australia'
        assert get_response_data[2]['location']['city'] == 'Perth'
        assert get_response.status_code == HttpStatus.ok_200.value

    def test_leisure_get_abbreviation_country_none_city_none(self,client,create_user,login, mock_environment_variables, mock_boto3_s3):
        create_currency(client, mock_environment_variables)
        create_location(client, mock_environment_variables)
        create_leisure(client, mock_environment_variables)
        get_first_page_response = client.get('/v1/leisure?abbreviation=AUD',
            headers = {"Content-Type": "application/json",
            "Authorization": f"Bearer {login['auth_token']}"})
        get_first_page_response_data = json.loads(get_first_page_response.get_data(as_text = True))
        assert len(get_first_page_response_data['leisure data']) == 6
        assert get_first_page_response_data['leisure data'][0]['activity'] == 'Cinema International Release'
        assert get_first_page_response_data['leisure data'][0]['price'] == 19.81
        assert get_first_page_response_data['leisure data'][0]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][0]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][0]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][1]['activity'] == 'Cinema International Release'
        assert get_first_page_response_data['leisure data'][1]['price'] == 22.97
        assert get_first_page_response_data['leisure data'][1]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][1]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][1]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][2]['activity'] == 'Gym Membership (Monthly)'
        assert get_first_page_response_data['leisure data'][2]['price'] == 76.03
        assert get_first_page_response_data['leisure data'][2]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][2]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][2]['location']['city'] == 'Perth'
        assert get_first_page_response_data['leisure data'][3]['activity'] == 'Gym Membership (Monthly)'
        assert get_first_page_response_data['leisure data'][3]['price'] == 137.08
        assert get_first_page_response_data['leisure data'][3]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][3]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][3]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][4]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_first_page_response_data['leisure data'][4]['price'] == 13.72
        assert get_first_page_response_data['leisure data'][4]['location']['id'] == 2
        assert get_first_page_response_data['leisure data'][4]['location']['country'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][4]['location']['city'] == 'Hong Kong'
        assert get_first_page_response_data['leisure data'][5]['activity'] == 'Tennis Court Rent (1hr)'
        assert get_first_page_response_data['leisure data'][5]['price'] == 23.13
        assert get_first_page_response_data['leisure data'][5]['location']['id'] == 1
        assert get_first_page_response_data['leisure data'][5]['location']['country'] == 'Australia'
        assert get_first_page_response_data['leisure data'][5]['location']['city'] == 'Perth'
        assert get_first_page_response_data['count'] == 6
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