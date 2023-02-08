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
    post_response_data = json.loads(post_response.get_data(as_text = True))
    assert post_response_data['message'] == 'successfully registered'
    assert post_response.status_code == HttpStatus.created_201.value
    assert User.query.count() == 1
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
def login(create_user,client):
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










    
