import json
import os
from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource
from httpstatus import HttpStatus
from models import (User,UserSchema,BlacklistToken,Currency,CurrencySchema,Location,LocationSchema,
Home_Purchase,Home_PurchaseSchema,Rent,RentSchema,Utilities,UtilitiesSchema,
Transportation,TransportationSchema,Food_and_Beverage, Food_and_BeverageSchema,
Childcare,ChildcareSchema,Apparel, ApparelSchema, Leisure,LeisureSchema)
from helpers import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, Float
from dotenv import load_dotenv
from datetime import datetime

'''Only admin can perform post, patch and delete operations on all resources except User'''

# Load environment variables from .env file
load_dotenv()

# Create API using blueprint + assign schemas to variables
cost_of_living_blueprint = Blueprint('cost_of_living', __name__)
user_schema = UserSchema()
currency_schema = CurrencySchema()
location_schema = LocationSchema()
home_purchase_schema = Home_PurchaseSchema()
rent_schema = RentSchema()
utilities_schema = UtilitiesSchema()
transportation_schema = TransportationSchema()
food_and_beverage_schema = Food_and_BeverageSchema()
childcare_schema = ChildcareSchema()
apparel_schema = ApparelSchema()
leisure_schema = LeisureSchema()
cost_of_living = Api(cost_of_living_blueprint)

class UserResource(Resource):
    # Allows users to retrieve information about their account using authorisation token
    def get(self):
        auth_header = request.headers['Authorization']
        if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]
            except IndexError:
                response = {'message': 'Bearer token malformed'}
                return response, HttpStatus.unauthorized_401.value

        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp,str):
                user = User.query.filter_by(id = resp).first()
                response = {'data': {
                    'user_id': user.id,
                    'email' : user.email,
                    'creation_date': str(user.creation_date)
                    }
                }
                return response, HttpStatus.ok_200.value
            response = {'message': resp}
            return response, HttpStatus.unauthorized_401.value
        else:
            response = {'message' : 'Provide a valid auth token'}
            return response, HttpStatus.forbidden_403.value

    # User registration  
    def post(self):
        user_register_dict = request.get_json()
        request_not_empty(user_register_dict)
        validate_request(user_schema,user_register_dict)

        user = User.query.filter_by(email = user_register_dict['email']).first()
        if not user and not user_register_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                user = User(email = user_register_dict['email'])
                user.check_password_strength_and_hash_if_ok(user_register_dict['password'])
                user.add(user)
                response = {'message': 'successfully registered'}
                return response, HttpStatus.created_201.value

            except Exception as e:
                response = {'message' : 'Error. Please try again'}
                return response, HttpStatus.unauthorized_401.value
        
        elif not user and user_register_dict['admin'] == os.environ.get('ADMIN_KEY'):
            try:
                user = User(email = user_register_dict['email'],admin = True)
                user.check_password_strength_and_hash_if_ok(user_register_dict['password'])
                user.add(user)
                response = {'message': 'successfully registered with admin privileges'}
                return response, HttpStatus.created_201.value
            
            except Exception as e:
                response = {'message' : 'Error. Please try again'}
                return response, HttpStatus.unauthorized_401.value
        
        else:
            response = {'message' : 'User already exists. Please log in'}
            return response, HttpStatus.conflict_409.value

class LoginResource(Resource):
    # User login
    def post(self):
        user_dict = request.get_json()
        request_not_empty(user_dict)
        validate_request(user_schema,user_dict)

        try:
            user = User.query.filter_by(email = user_dict['email']).first()
            if user and user.verify_password(user_dict['password']):
                auth_token = user.encode_auth_token(user.id)
                if auth_token:
                    response = {
                    'message': 'successfully logged in',
                    'auth_token': auth_token.decode()}
                    return response, HttpStatus.ok_200.value
            else:
                response = {'message': 'User does not exist'}
                return response, HttpStatus.notfound_404.value
        
        except Exception as e:
            print(e)
            response = {'message': 'Try again'}
            return response, HttpStatus.internal_server_error.value

class LogoutResource(Resource):
    # User logout using provided auth token
    def post(self):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]
            except IndexError:
                response = {'message': 'Bearer token malformed'}
                return response, HttpStatus.unauthorized_401.value
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp,str):
                blacklist_token = BlacklistToken(token = auth_token)
                try:
                    blacklist_token.add(blacklist_token)
                    response = {'message' : 'Successfully logged out'}
                    return response, HttpStatus.ok_200.value
                except Exception as e:
                    response = {'message': e}
                    return response, HttpStatus.bad_request_400.value
            else:
                response = {'message' : resp}
                return response, HttpStatus.unauthorized_401.value
            
        else:
            response = {'message' : 'Provide a valid auth token'}
            return response, HttpStatus.forbidden_403.value

class ResetPasswordResource(Resource):
    # Resets user password
    def post(self):
        reset_password_dict = request.get_json()
        request_not_empty(reset_password_dict)
        validate_request(user_schema,reset_password_dict)
        
        try:
            user = User.query.filter_by(email = reset_password_dict['email']).first()
            if user:
                user.check_password_strength_and_hash_if_ok(reset_password_dict['password'])
                response = {'message': 'Password reset successful'}
                return response, HttpStatus.ok_200.value
            else:
                response = {'message': 'User does not exist'}
                return response, HttpStatus.unauthorized_401.value
        
        except Exception as e:
            print(e)
            response = {'message': 'Try again'}
            return response, HttpStatus.internal_server_error.value
            
class CurrencyResource(Resource):
    # Retrieves USD/local currency exchange rate for specific id or all currencies
    def get(self,id=None):

        if authenticate_jwt() == True:

            if id != None:
                currency = Currency.query.get_or_404(id)
                dumped_currency = currency_schema.dump(currency)
                return dumped_currency
        
            else:
                pagination_helper = PaginationHelper(
                    request,
                    query = Currency.query,
                    resource_for_url = 'cost_of_living.currencyresource',
                    key_name = 'results',
                    schema = currency_schema
                )
                paginated_currencies = pagination_helper.paginate_query()
                return paginated_currencies
    
    # Creates a new currency
    def post(self):
        currency_dict = request.get_json()
        request_not_empty(currency_dict)
        validate_request(currency_schema,currency_dict)
        
        if currency_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            if not Currency.is_abbreviation_unique(id=0,abbreviation = currency_dict['abbreviation']):
                response = {'message': f"Error currency abbreviation {currency_dict['abbreviation']} already exists"}
                return response, HttpStatus.bad_request_400.value

            try:
                currency = Currency(abbreviation = currency_dict['abbreviation'],
                usd_to_local_exchange_rate = currency_dict['usd_to_local_exchange_rate'])
                currency.add(currency)
                query = Currency.query.get(currency.id)
                dump_result = currency_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates abbreviation and exchange rate for specific currency id
    def patch(self,id):
        currency = Currency.query.get_or_404(id)
        
        currency_dict = request.get_json(force = True)
        request_not_empty(currency_dict)
        validate_request(currency_schema,currency_dict)

        if currency_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'abbreviation' in currency_dict and currency_dict['abbreviation'] != None:
                    currency.abbreviation = currency_dict['abbreviation']
                if 'usd_to_local_exchange_rate' in currency_dict and \
                currency_dict['usd_to_local_exchange_rate'] != None:
                    currency.usd_to_local_exchange_rate = currency_dict['usd_to_local_exchange_rate']
                currency.last_updated = datetime.now()
            
                currency.update()
                self.get(id)

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes currency
    def delete(self,id):
        admin_dict = request.get_json()
        currency = Currency.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                currency.delete(currency)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class LocationListResource(Resource):
    # Retrieve information regarding specific location id or information regarding all locations
    def get(self,id=None):

        if authenticate_jwt() == True:

            if id != None:
                location = Location.query.get_or_404(id)
                dumped_location = location_schema.dump(location)
                return dumped_location

            else:
                pagination_helper = PaginationHelper(
                    request,
                    query = Location.query,
                    resource_for_url = 'cost_of_living.locationlistresource',
                    key_name = 'results',
                    schema = location_schema
                )
                paginated_locations = pagination_helper.paginate_query()
                return paginated_locations
    # Creates a new location
    def post(self):
        location_dict = request.get_json()
        request_not_empty(location_dict)
        validate_request(location_schema,location_dict)

        if location_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                currency_abbreviation = location_dict['abbreviation']
                currency = Currency.query.filter_by(abbreviation = currency_abbreviation).first()

                if currency is None:
                    response = {'message': 'Specified currency doesnt exist in /currencies/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                location = Location(country = location_dict['country'], city = location_dict['city'], currency = currency)
                location.add(location)
                query = Location.query.get(location.id)
                dump_result = location_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes location
    def delete(self,id):
        admin_dict = request.get_json()
        location = Location.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location.delete(location)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class HomePurchaseResource(Resource):
    # Retrieves home purchase price characteristics from a specified id, country, city, abbreviation or combination of the prior three.
    def get(self,id=None):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:

            if id != None:
                home_purchase = Home_Purchase.query.get_or_404(id)
                dumped_home_purchase = home_purchase_schema.dump(home_purchase)
                return dumped_home_purchase
        
            qry = orm.session.query(Home_Purchase).join(Location, Home_Purchase.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Home_Purchase.property_location.asc(),Home_Purchase.price_per_sqm.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_home_purchase = home_purchase_schema.dump(qry_res,many=True)
                    for result in dumped_home_purchase:
                        result['price_per_sqm'] = round(result['price_per_sqm'] * conversion,2)
                    return dumped_home_purchase
                
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.homepurchaseresource',
                    key_name = 'results',   
                    schema = home_purchase_schema
                    )
                    dumped_home_purchase = pagination_helper.paginate_query()
                    for result in dumped_home_purchase['results']:
                        result['price_per_sqm'] = round(result['price_per_sqm'] * conversion,2)
                    return dumped_home_purchase
            
            else:
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                    qry_res = qry.all()
                    dumped_home_purchase = home_purchase_schema.dump(qry_res,many=True)
                    return dumped_home_purchase
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query = qry,
                resource_for_url = 'cost_of_living.homepurchaseresource',
                key_name = 'results',   
                schema = home_purchase_schema
                )
                dumped_home_purchase = pagination_helper.paginate_query()
                return dumped_home_purchase
    
    # Creates an record for relevant purchasing costs of buying a property in a particular location
    def post(self):
        home_purchase_dict = request.get_json()
        request_not_empty(home_purchase_dict)
        validate_request(home_purchase_schema,home_purchase_dict)

        if home_purchase_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location_city = home_purchase_dict['city']
                location = Location.query.filter_by(city = location_city).first()

                if location is None:
                    response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                home_purchase = Home_Purchase(property_location = home_purchase_dict['property_location'], 
                price_per_sqm = home_purchase_dict['price_per_sqm'], 
                mortgage_interest = home_purchase_dict['mortgage_interest'],
                location = location)
                home_purchase.add(home_purchase)
                query = Home_Purchase.query.get(home_purchase.id)
                dump_result = home_purchase_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates property location, price per sqm and mortgage interest rate for specified record
    def patch(self,id):
        home_purchase = Home_Purchase.query.get_or_404(id)
        
        home_purchase_dict = request.get_json(force = True)
        request_not_empty(home_purchase_dict)
        validate_request(home_purchase_schema,home_purchase_dict)

        if home_purchase_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'property_location' in home_purchase_dict and home_purchase_dict['property_location'] != None:
                    home_purchase.property_location = home_purchase_dict['property_location']
                if 'price_per_sqm' in home_purchase_dict and \
                home_purchase_dict['price_per_sqm'] != None:
                    home_purchase.price_per_sqm = home_purchase_dict['price_per_sqm']
                if 'mortgage_interest' in home_purchase_dict and \
                home_purchase_dict['mortgage_interest'] != None:
                    home_purchase.mortgage_interest = home_purchase_dict['mortgage_interest']
            
                home_purchase.update()
                self.get(id)

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
            
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes Home_Purchase record
    def delete(self,id):
        admin_dict = request.get_json()
        home_purchase = Home_Purchase.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                home_purchase.delete(home_purchase)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class RentResource(Resource):
    # Retrieves rental costs from a specified id, country, city, abbreviation or combination of the prior three.
    def get(self,id=None):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:

            if id != None:
                rent = Rent.query.get_or_404(id)
                dumped_rent = rent_schema.dump(rent)
                return dumped_rent
        
            qry = orm.session.query(Rent).join(Location, Rent.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Rent.property_location.asc(),Rent.bedrooms.asc(),Rent.monthly_price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_rent = rent_schema.dump(qry_res,many=True)
                    for result in dumped_rent:
                        result['monthly_price'] = round(result['monthly_price'] * conversion,2)
                    return dumped_rent
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.rentresource',
                    key_name = 'results',   
                    schema = rent_schema
                    )
                    dumped_rent = pagination_helper.paginate_query()
                    for result in dumped_rent['results']:
                        result['monthly_price'] = round(result['monthly_price'] * conversion,2)
                    return dumped_rent
            
            else:
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                    qry_res = qry.all()
                    dumped_rent = rent_schema.dump(qry_res,many=True)
                    return dumped_rent
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query = qry,
                resource_for_url = 'cost_of_living.rentresource',
                key_name = 'results',   
                schema = rent_schema
                )
                dumped_rent = pagination_helper.paginate_query()
                return dumped_rent

    # Creates a record of rental costs for a particular location
    def post(self):
        rent_dict = request.get_json()
        request_not_empty(rent_dict)
        validate_request(rent_schema,rent_dict)

        if rent_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location_city = rent_dict['city']
                location = Location.query.filter_by(city = location_city).first()

                if location is None:
                    response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                rent = Rent(property_location = rent_dict['property_location'], 
                bedrooms = rent_dict['bedrooms'], monthly_price = rent_dict['monthly_price'],
                location = location)
                rent.add(rent)
                query = Rent.query.get(rent.id)
                dump_result = rent_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates property location, number of bedrooms and monthly price for a particular rental record
    def patch(self,id):
        rent = Rent.query.get_or_404(id)
        
        rent_dict = request.get_json(force = True)
        request_not_empty(rent_dict)
        validate_request(rent_schema,rent_dict)

        if rent_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'property_location' in rent_dict and rent_dict['property_location'] != None:
                    rent.property_location = rent_dict['property_location']
                if 'bedrooms' in rent_dict and \
                rent_dict['bedrooms'] != None:
                    rent.bedrooms = rent_dict['bedrooms']
                if 'monthly_price' in rent_dict and \
                rent_dict['monthly_price'] != None:
                    rent.monthly_price = rent_dict['monthly_price']
            
                rent.update()
                self.get(id)

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes Rent record
    def delete(self,id):
        admin_dict = request.get_json()
        rent = Rent.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                rent.delete(rent)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class UtilitiesResource(Resource):
    # Retrieves information regarding a utility from a given id, country, city, abbreviation or combination of the three.
    def get(self,id=None):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:

            if id != None:
                utilities = Utilities.query.get_or_404(id)
                dumped_utilities = utilities_schema.dump(utilities)
                return dumped_utilities
        
            qry = orm.session.query(Utilities).join(Location, Utilities.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Utilities.utility.asc(),Utilities.monthly_price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_utilities = utilities_schema.dump(qry_res,many=True)
                    for result in dumped_utilities:
                        result['monthly_price'] = round(result['monthly_price'] * conversion,2)
                    return dumped_utilities
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.utilitiesresource',
                    key_name = 'results',   
                    schema = utilities_schema
                    )
                    dumped_utilities = pagination_helper.paginate_query()
                    for result in dumped_utilities['results']:
                        result['monthly_price'] = round(result['monthly_price'] * conversion,2)
                    return dumped_utilities
            
            else:
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                    qry_res = qry.all()
                    dumped_utilities = utilities_schema.dump(qry_res,many=True)
                    return dumped_utilities
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query = qry,
                resource_for_url = 'cost_of_living.utilitiesresource',
                key_name = 'results',   
                schema = utilities_schema
                )
                dumped_utilities = pagination_helper.paginate_query()
                return dumped_utilities
    
    # Creates a new utility record
    def post(self):
        utilities_dict = request.get_json()
        request_not_empty(utilities_dict)
        validate_request(utilities_schema,utilities_dict)

        if utilities_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location_city = utilities_dict['city']
                location = Location.query.filter_by(city = location_city).first()

                if location is None:
                    response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                utilities = Utilities(utility = utilities_dict['utility'], 
                monthly_price = utilities_dict['monthly_price'],
                location = location)
                utilities.add(utilities)
                query = Utilities.query.get(utilities.id)
                dump_result = utilities_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value   
    
    # Updates utility name, monthly price for a given utility
    def patch(self,id):
        utilities = Utilities.query.get_or_404(id)
        
        utilities_dict = request.get_json(force = True)
        request_not_empty(utilities_dict)
        validate_request(utilities_schema,utilities_dict)

        if utilities_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'utility' in utilities_dict and utilities_dict['utility'] != None:
                    utilities.utility = utilities_dict['utility']
                if 'monthly_price' in utilities_dict and \
                utilities_dict['monthly_price'] != None:
                    utilities.monthly_price = utilities_dict['monthly_price']
            
                utilities.update()
                self.get(id)

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes Utilities record
    def delete(self,id):
        admin_dict = request.get_json()
        utilities = Utilities.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                utilities.delete(utilities)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class TransportationResource(Resource):
    # Retrieves information for a particular mode of transport from a particular id, country, city, abbreviation or combination of the last three.
    def get(self,id=None):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:

            if id != None:
                transportation = Transportation.query.get_or_404(id)
                dumped_transportation = transportation_schema.dump(transportation)
                return dumped_transportation
        
            qry = orm.session.query(Transportation).join(Location, Transportation.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Transportation.type.asc(),Transportation.price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_transportation = transportation_schema.dump(qry_res,many=True)
                    for result in dumped_transportation:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_transportation
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.transportationresource',
                    key_name = 'results',   
                    schema = transportation_schema
                    )
                    dumped_transportation = pagination_helper.paginate_query()
                    for result in dumped_transportation['results']:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_transportation
            
            else:
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                    qry_res = qry.all()
                    dumped_transportation = transportation_schema.dump(qry_res,many=True)
                    return dumped_transportation
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query = qry,
                resource_for_url = 'cost_of_living.transportationresource',
                key_name = 'results',   
                schema = transportation_schema
                )
                dumped_transportation = pagination_helper.paginate_query()
                return dumped_transportation
    
    # Creates a new record for a mode of transport
    def post(self):
        transportation_dict = request.get_json()
        request_not_empty(transportation_dict)
        validate_request(transportation_schema,transportation_dict)

        if transportation_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location_city = transportation_dict['city']
                location = Location.query.filter_by(city = location_city).first()

                if location is None:
                    response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                transportation = Transportation(type = transportation_dict['type'], 
                price = transportation_dict['price'],
                location = location)
                transportation.add(transportation)
                query = Transportation.query.get(transportation.id)
                dump_result = transportation_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates type and price for a particular record
    def patch(self,id):
        transportation = Transportation.query.get_or_404(id)
        
        transportation_dict = request.get_json(force = True)
        request_not_empty(transportation_dict)
        validate_request(transportation_schema,transportation_dict)

        if transportation_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'type' in transportation_dict and transportation_dict['type'] != None:
                    transportation.type = transportation_dict['type']
                if 'price' in transportation_dict and \
                transportation_dict['price'] != None:
                    transportation.price = transportation_dict['price']
            
                transportation.update()
                self.get(id)

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes Transportation record
    def delete(self,id):
        admin_dict = request.get_json()
        transportation = Transportation.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                transportation.delete(transportation)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class FoodBeverageResource(Resource):
    # Retrieves information regarding a food and beverage item from a particular id, country, city, abbreviation or combination of the three.
    def get(self,id=None):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:

            if id != None:
                food_and_beverage = Food_and_Beverage.query.get_or_404(id)
                dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage)
                return dumped_food_and_beverage
        
            qry = orm.session.query(Food_and_Beverage).join(Location, Food_and_Beverage.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Food_and_Beverage.item_category.asc(),Food_and_Beverage.purchase_point.asc(),Food_and_Beverage.item.asc(),
            Food_and_Beverage.price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_food_and_beverage = food_and_beverage_schema.dump(qry_res,many=True)
                    for result in dumped_food_and_beverage:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_food_and_beverage
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.foodbeverageresource',
                    key_name = 'results',   
                    schema = food_and_beverage_schema
                    )
                    dumped_food_and_beverage = pagination_helper.paginate_query()
                    for result in dumped_food_and_beverage['results']:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_food_and_beverage
            
            else:
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                    qry_res = qry.all()
                    dumped_food_and_beverage = food_and_beverage_schema.dump(qry_res,many=True)
                    return dumped_food_and_beverage
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query = qry,
                resource_for_url = 'cost_of_living.foodbeverageresource',
                key_name = 'results',   
                schema = food_and_beverage_schema
                )
                dumped_food_and_beverage = pagination_helper.paginate_query()
                return dumped_food_and_beverage
    
    # Creates a new record for food and beverage item
    def post(self):
        food_and_beverage_dict = request.get_json()
        request_not_empty(food_and_beverage_dict)
        validate_request(food_and_beverage_schema,food_and_beverage_dict)

        if food_and_beverage_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location_city = food_and_beverage_dict['city']
                location = Location.query.filter_by(city = location_city).first()

                if location is None:
                    response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                food_and_beverage = Food_and_Beverage(item_category = food_and_beverage_dict['item_category'], 
                purchase_point = food_and_beverage_dict['purchase_point'],
                item = food_and_beverage_dict['item'],
                price = food_and_beverage_dict['price'],
                location = location)
                food_and_beverage.add(food_and_beverage)
                query = Food_and_Beverage.query.get(food_and_beverage.id)
                dump_result = food_and_beverage_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates item category, purchase point, item and price for a given item
    def patch(self,id):
        food_and_beverage = Food_and_Beverage.query.get_or_404(id)
        
        food_and_beverage_dict = request.get_json(force = True)
        request_not_empty(food_and_beverage_dict)
        validate_request(food_and_beverage_schema,food_and_beverage_dict)

        if food_and_beverage_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'item_category' in food_and_beverage_dict and food_and_beverage_dict['item_category'] != None:
                    food_and_beverage.item_category = food_and_beverage_dict['item_category']
                if 'purchase_point' in food_and_beverage_dict and \
                food_and_beverage_dict['purchase_point'] != None:
                    food_and_beverage.purchase_point = food_and_beverage_dict['purchase_point']
                if 'item' in food_and_beverage_dict and \
                food_and_beverage_dict['item'] != None:
                    food_and_beverage.item = food_and_beverage_dict['item']
                if 'price' in food_and_beverage_dict and \
                food_and_beverage_dict['price'] != None:
                    food_and_beverage.price = food_and_beverage_dict['price']
            
                food_and_beverage.update()
                self.get(id)

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes Food_and_Beverage record
    def delete(self,id):
        admin_dict = request.get_json()
        food_and_beverage = Food_and_Beverage.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                food_and_beverage.delete(food_and_beverage)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class ChildcareResource(Resource):
    # Retrives information regarding childcare service from a given, id, country, city, abbreviation or combination of the last three.
    def get(self,id=None):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:

            if id != None:
                childcare = Childcare.query.get_or_404(id)
                dumped_childcare = childcare_schema.dump(childcare)
                return dumped_childcare
        
            qry = orm.session.query(Childcare).join(Location, Childcare.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Childcare.type.asc(),Childcare.annual_price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_childcare = childcare_schema.dump(qry_res,many=True)
                    for result in dumped_childcare:
                        result['annual_price'] = round(result['annual_price'] * conversion,2)
                    return dumped_childcare
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.childcareresource',
                    key_name = 'results',   
                    schema = childcare_schema
                    )
                    dumped_childcare = pagination_helper.paginate_query()
                    for result in dumped_childcare['results']:
                        result['annual_price'] = round(result['annual_price'] * conversion,2)
                    return dumped_childcare
            
            else:
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                    qry_res = qry.all()
                    dumped_childcare = childcare_schema.dump(qry_res,many=True)
                    return dumped_childcare
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query = qry,
                resource_for_url = 'cost_of_living.childcareresource',
                key_name = 'results',   
                schema = childcare_schema
                )
                dumped_childcare = pagination_helper.paginate_query()
                return dumped_childcare
    
    # Creates a new childcare record
    def post(self):
        childcare_dict = request.get_json()
        request_not_empty(childcare_dict)

        if childcare_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location_city = childcare_dict['city']
                location = Location.query.filter_by(city = location_city).first()

                if location is None:
                    response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                childcare = Childcare(type = childcare_dict['type'],
                annual_price = childcare_dict['annual_price'],
                location = location)
                childcare.add(childcare)
                query = Childcare.query.get(childcare.id)
                dump_result = childcare_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates type and annual price information for a given childcare service
    def patch(self,id):
        childcare = Childcare.query.get_or_404(id)
        
        childcare_dict = request.get_json(force = True)
        request_not_empty(childcare_dict)
        validate_request(childcare_schema,childcare_dict)

        if childcare_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'type' in childcare_dict and childcare_dict['type'] != None:
                    childcare.type = childcare_dict['type']
                if 'annual_price' in childcare_dict and \
                childcare_dict['annual_price'] != None:
                    childcare.annual_price = childcare_dict['annual_price']
            
                childcare.update()
                self.get(id)

            except SQLAlchemyError as e:
                orm.session.rollback()
                response = {"error": str(e)}
                return response, HttpStatus.bad_request_400.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes Childcare record
    def delete(self,id):
        admin_dict = request.get_json()
        childcare = Childcare.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                childcare.delete(childcare)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class ApparelResource(Resource):
    # Retrieves information for a given apparel item from a particular, id, country, city, abbreviation or combination of the three. 
    def get(self,id=None):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:

            if id != None:
                apparel = Apparel.query.get_or_404(id)
                dumped_apparel = apparel_schema.dump(apparel)
                return dumped_apparel
        
            qry = orm.session.query(Apparel).join(Location, Apparel.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Apparel.item.asc(),Apparel.price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_apparel = apparel_schema.dump(qry_res,many=True)
                    for result in dumped_apparel:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_apparel            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.apparelresource',
                    key_name = 'results',   
                    schema = apparel_schema
                    )
                    dumped_apparel = pagination_helper.paginate_query()
                    for result in dumped_apparel['results']:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_apparel
            
            else:
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                    qry_res = qry.all()
                    dumped_apparel = apparel_schema.dump(qry_res,many=True)
                    return dumped_apparel
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query = qry,
                resource_for_url = 'cost_of_living.apparelresource',
                key_name = 'results',   
                schema = apparel_schema
                )
                dumped_apparel = pagination_helper.paginate_query()
                return dumped_apparel
    
    # Creates a new apparel item
    def post(self):
        apparel_dict = request.get_json()
        request_not_empty(apparel_dict)
        validate_request(apparel_schema,apparel_dict)

        if apparel_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location_city = apparel_dict['city']
                location = Location.query.filter_by(city = location_city).first()

                if location is None:
                    response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                apparel = Apparel(item = apparel_dict['item'], 
                price = apparel_dict['price'],
                location = location)
                apparel.add(apparel)
                query = Apparel.query.get(apparel.id)
                dump_result = apparel_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates item name and price for a given piece of apparel
    def patch(self,id):
        apparel = Apparel.query.get_or_404(id)
        
        apparel_dict = request.get_json(force = True)
        request_not_empty(apparel_dict)
        validate_request(apparel_schema,apparel_dict)

        if apparel_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'item' in apparel_dict and apparel_dict['item'] != None:
                    apparel.item = apparel_dict['item']
                if 'price' in apparel_dict and \
                apparel_dict['price'] != None:
                    apparel.price = apparel_dict['price']
            
                apparel.update()
                self.get(id)

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

    # Deletes Apparel record
    def delete(self,id):
        admin_dict = request.get_json()
        apparel = Apparel.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                apparel.delete(apparel)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class LeisureResource(Resource):
    # Retrieves information for a given leisure acitivty from a given id, country, city, abbreviation or combination of the three.
    def get(self,id=None):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:

            if id != None:
                leisure = Leisure.query.get_or_404(id)
                dumped_leisure = leisure_schema.dump(leisure)
                return dumped_leisure
        
            qry = orm.session.query(Leisure).join(Location, Leisure.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Leisure.activity.asc(),Leisure.price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_leisure = leisure_schema.dump(qry_res,many=True)
                    for result in dumped_leisure:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_leisure            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.leisureresource',
                    key_name = 'results',   
                    schema = leisure_schema
                    )
                    dumped_leisure = pagination_helper.paginate_query()
                    for result in dumped_leisure['results']:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_leisure
            
            else:
                if country:
                    qry = qry.filter(Location.country==country)
                if city:
                    qry= qry.filter(Location.city==city)
                    qry_res = qry.all()
                    dumped_leisure = leisure_schema.dump(qry_res,many=True)
                    return dumped_leisure
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query = qry,
                resource_for_url = 'cost_of_living.leisureresource',
                key_name = 'results',   
                schema = leisure_schema
                )
                dumped_leisure = pagination_helper.paginate_query()
                return dumped_leisure
    
    # Creates a new leisure activity
    def post(self):
        leisure_dict = request.get_json()
        request_not_empty(leisure_dict)
        validate_request(leisure_schema,leisure_dict)

        if leisure_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location_city = leisure_dict['city']
                location = Location.query.filter_by(city = location_city).first()

                if location is None:
                    response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                    return response, HttpStatus.notfound_404.value
                
                leisure = Leisure(activity = leisure_dict['activity'], 
                price = leisure_dict['price'],
                location = location)
                leisure.add(leisure)
                query = Leisure.query.get(leisure.id)
                dump_result = leisure_schema.dump(query)
                return dump_result, HttpStatus.created_201.value

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates activity name and price information for a given leisure activity
    def patch(self,id):
        leisure = Leisure.query.get_or_404(id)
        
        leisure_dict = request.get_json(force = True)
        request_not_empty(leisure_dict)
        validate_request(leisure_schema,leisure_dict)

        if leisure_dict.get('admin') == os.environ.get('ADMIN_KEY'):

            try:
                if 'activity' in leisure_dict and leisure_dict['activity'] != None:
                    leisure.activity = leisure_dict['activity']
                if 'price' in leisure_dict and \
                leisure_dict['price'] != None:
                    leisure.price = leisure_dict['price']
            
                leisure.update()
                self.get(id)

            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Deletes Leisure record
    def delete(self,id):
        admin_dict = request.get_json()
        leisure = Leisure.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                leisure.delete(leisure)
                response = {'message': 'Successfully deleted'}
                return response, HttpStatus.no_content_204.value
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

cost_of_living.add_resource(UserResource,'/auth/user')
cost_of_living.add_resource(LoginResource,'/auth/login')
cost_of_living.add_resource(LogoutResource, '/auth/logout')
cost_of_living.add_resource(ResetPasswordResource,'/user/password_reset')        
cost_of_living.add_resource(CurrencyResource, '/currencies','/currencies/<int:id>')
cost_of_living.add_resource(LocationListResource, '/locations','/locations/<int:id>')
cost_of_living.add_resource(HomePurchaseResource, '/homepurchase','/homepurchase/<int:id>')
cost_of_living.add_resource(RentResource, '/rent','/rent/<int:id>')
cost_of_living.add_resource(UtilitiesResource, '/utilities','/utilities/<int:id>')
cost_of_living.add_resource(TransportationResource, '/transportation', '/transportation/<int:id>')
cost_of_living.add_resource(FoodBeverageResource,'/foodbeverage', '/foodbeverage/<int:id>')
cost_of_living.add_resource(ChildcareResource,'/childcare', '/childcare/<int:id>')
cost_of_living.add_resource(ApparelResource, '/apparel', '/apparel/<int:id>')
cost_of_living.add_resource(LeisureResource, '/leisure', '/leisure/<int:id>')