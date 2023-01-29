from httpstatus import *
from models import orm
from flask import make_response

def request_not_empty(dict):
    if dict == False:
        response = {'message': 'No input data provided'}
        return response, HttpStatus.bad_request_400.value

def validate_request(schema,dict):
    errors = schema.validate(dict)
    if errors:
        return errors, HttpStatus.bad_request_400.value

def sql_alchemy_error_response(error):
    orm.session.rollback()
    response = {'error': str(error)}
    return response, HttpStatus.bad_request_400.value

def delete_object(object):
    object.delete(object)
    response = make_response()
    return response, HttpStatus.no_content_204.value
