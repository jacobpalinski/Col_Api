import json
import os
import boto3
import botocore
from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource
from httpstatus import HttpStatus
from models import (User, UserSchema, BlacklistToken, Currency, CurrencySchema, Location, LocationSchema,
HomePurchase, HomePurchaseSchema, Rent, RentSchema, Utilities, UtilitiesSchema,
Transportation, TransportationSchema, FoodBeverage, FoodBeverageSchema,
Childcare, ChildcareSchema, Apparel, ApparelSchema, Leisure, LeisureSchema, INCLUDE)
from helpers import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, Float
from dotenv import load_dotenv
from datetime import datetime
from flasgger import swag_from

'''Only admin can perform post, patch and delete operations on all resources except User'''

# Load environment variables from .env file
load_dotenv()

# Create API using blueprint + assign schemas to variables
cost_of_living_blueprint = Blueprint('cost_of_living', __name__)
user_schema = UserSchema()
currency_schema = CurrencySchema()
location_schema = LocationSchema()
home_purchase_schema = HomePurchaseSchema()
rent_schema = RentSchema()
utilities_schema = UtilitiesSchema()
transportation_schema = TransportationSchema()
foodbeverage_schema = FoodBeverageSchema()
childcare_schema = ChildcareSchema()
apparel_schema = ApparelSchema()
leisure_schema = LeisureSchema()
cost_of_living = Api(cost_of_living_blueprint)

class UserResource(Resource):
    # Allows users to retrieve information about their account using authorisation token
    @swag_from('swagger/userresource_get.yml')
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
            if not isinstance(resp, str):
                user = User.query.filter_by(id=resp).first()
                response = {'details': {
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
    @swag_from('swagger/userresource_post.yml')
    def post(self):
        user_register_dict = request.get_json()
        try:
            user_schema.load(user_register_dict, unknown=INCLUDE)
        except ValidationError:
            response = {'message': 'Invalid email address'}
            return response, HttpStatus.bad_request_400.value

        user = User.query.filter_by(email=user_register_dict['email']).first()
        if not user and not user_register_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                user = User(email=user_register_dict['email'])
                user.check_password_strength_and_hash_if_ok(user_register_dict['password'])
                user.add(user)
                response = {'message': 'Successfully registered'}
                return response, HttpStatus.created_201.value

            except Exception as e:
                response = {'message' : 'Invalid password'}
                return response, HttpStatus.unauthorized_401.value
        
        elif not user and user_register_dict['admin'] == os.environ.get('ADMIN_KEY'):
            try:
                user = User(email=user_register_dict['email'], admin=True)
                user.check_password_strength_and_hash_if_ok(user_register_dict['password'])
                user.add(user)
                response = {'message': 'Successfully registered with admin privileges'}
                return response, HttpStatus.created_201.value
            
            except Exception as e:
                response = {'message' : 'Invalid password'}
                return response, HttpStatus.unauthorized_401.value
        
        else:
            response = {'message' : 'User already exists. Please log in'}
            return response, HttpStatus.conflict_409.value

class LoginResource(Resource):
    # User login
    @swag_from('swagger/loginresource_post.yml')
    def post(self):
        user_dict = request.get_json()
        try:
            user_schema.load(user_dict)
        except ValidationError:
            response = {'message': 'Invalid email address'}
            return response, HttpStatus.bad_request_400.value

        try:
            user = User.query.filter_by(email=user_dict['email']).first()
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
    @swag_from('swagger/logoutresource_post.yml')
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
            if not isinstance(resp, str):
                blacklist_token = BlacklistToken(token=auth_token)
                try:
                    blacklist_token.add(blacklist_token)
                    response = {'message' : 'Successfully logged out'}
                    return response, HttpStatus.ok_200.value
                except Exception as e:
                    response = {'message': e}
                    return response, HttpStatus.bad_request_400.value
            else:
                response = {'message' : 'Provide a valid auth token'}
                return response, HttpStatus.forbidden_403.value  
        else:
            response = {'message' : 'Provide a valid auth token'}
            return response, HttpStatus.forbidden_403.value

class ResetPasswordResource(Resource):
    # Resets user password
    @swag_from('swagger/resetpasswordresource_post.yml')
    def post(self):
        reset_password_dict = request.get_json()
        try:
            user_schema.load(reset_password_dict)
        except ValidationError:
            response = {'message': 'Invalid email address'}
            return response, HttpStatus.bad_request_400.value
        
        try:
            user = User.query.filter_by(email=reset_password_dict['email']).first()
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
    # Retrieves USD/local currency exchange rate for specified id
    @swag_from('swagger/currencyresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:
            currency = Currency.query.get_or_404(id)
            dumped_currency = currency_schema.dump(currency)
            return dumped_currency
    
    def delete(self, id):
        admin_dict = request.get_json()
        currency = Currency.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                currency.delete(currency)
                response = {'message': 'Currency id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class CurrencyListResource(Resource):
    # Retrieves USD/local currency exchange rate for all currencies
    @swag_from('swagger/currencylistresource_get.yml')
    def get(self):
        if authenticate_jwt() == True:
            pagination_helper = PaginationHelper(
                request,
                query = Currency.query,
                resource_for_url = 'cost_of_living.currencylistresource',
                key_name = 'currencies',
                schema = currency_schema
                )
            paginated_currencies = pagination_helper.paginate_query()
            return paginated_currencies
    
    # Adds currencies from latest locations_with_currencies file from S3 transformed bucket to api endpoint
    def post(self):
        currency_dict = request.get_json()
        
        if currency_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                locations_with_currencies_data = get_data(file_prefix='locations_with_currencies')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new currencies added
            currencies_added = 0

            for data in locations_with_currencies_data:
                if not Currency.is_unique(abbreviation=data['Abbreviation']):
                    continue
                try:
                    currency = Currency(abbreviation=data['Abbreviation'],
                    usd_to_local_exchange_rate=data['USD_to_local'])
                    currency.add(currency)
                    currencies_added += 1

                except SQLAlchemyError as e:
                    sql_alchemy_error_response(e)

            response = {'message': f'Successfully added {currencies_added} currencies'}
            return response, HttpStatus.created_201.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates abbreviation and exchange rate for abbreviation with modified exchange rates
    def patch(self):
        
        currency_dict = request.get_json(force=True)

        if currency_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                locations_with_currencies_data = get_data(file_prefix='locations_with_currencies')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value

            # Track currencies updated
            currencies_updated = 0

            for data in locations_with_currencies_data:
                try:
                    currency = Currency.query.filter_by(abbreviation=data['Abbreviation']).first()
                    if currency == None:
                        continue
                    elif data['USD_to_local'] != currency.usd_to_local_exchange_rate:
                        currency.usd_to_local_exchange_rate = data['USD_to_local']
                        currencies_updated += 1
                    else:
                        continue
                except SQLAlchemyError as e:
                    sql_alchemy_error_response(e)
            
            response = {'message': f'usd_to_local_exchange_rate was successfully updated for {currencies_updated} currencies'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class LocationResource(Resource):
    # Retrieve information from specific id
    @swag_from('swagger/locationresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:
            location = Location.query.get_or_404(id)
            dumped_location = location_schema.dump(location)
            return dumped_location
    
    # Deletes location
    def delete(self, id):
        admin_dict = request.get_json()
        location = Location.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                location.delete(location)
                response = {'message': 'Location id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class LocationListResource(Resource):
    # Retrieve information regarding all locations
    @swag_from('swagger/locationlistresource_get.yml')
    def get(self):
        if authenticate_jwt() == True:
            pagination_helper = PaginationHelper(
                request,
                query = Location.query,
                resource_for_url = 'cost_of_living.locationlistresource',
                key_name = 'locations',
                schema = location_schema
            )
            paginated_locations = pagination_helper.paginate_query()
            return paginated_locations
        
    # Creates a new location
    def post(self):
        location_dict = request.get_json()
        if location_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                locations_with_currencies_data = get_data(file_prefix='locations_with_currencies')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new locations added
            locations_added = 0

            for data in locations_with_currencies_data:
                if not Location.is_unique(country=data['Country'], city=data['City']):
                    continue
                try:
                    abbreviation = data['Abbreviation']
                    currency = Currency.query.filter_by(abbreviation=abbreviation).first()

                    if currency is None:
                        response = {'message': 'Specified currency doesnt exist in /currencies/ API endpoint'}
                        return response, HttpStatus.notfound_404.value
                
                    location = Location(country=data['Country'], city=data['City'], currency=currency)
                    location.add(location)
                    locations_added += 1

                except SQLAlchemyError as e:
                    sql_alchemy_error_response(e)

            response = {'message': f'Successfully added {locations_added} locations'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class HomePurchaseResource(Resource):
    # Retrieve home purchase price information from specific id
    @swag_from('swagger/homepurchaseresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:            
            home_purchase = HomePurchase.query.get_or_404(id)
            dumped_home_purchase = home_purchase_schema.dump(home_purchase)
            return dumped_home_purchase
    
    # Deletes HomePurchase record
    def delete(self, id):
        admin_dict = request.get_json()
        home_purchase = HomePurchase.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                home_purchase.delete(home_purchase)
                response = {'message': 'HomePurchase id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class HomePurchaseListResource(Resource):
    # Retrieves home purchase price information from a specified country, city, abbreviation, combination of the 3 or all ids
    @swag_from('swagger/homepurchaselistresource_get.yml')
    def get(self):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:
            qry = orm.session.query(HomePurchase).join(Location, HomePurchase.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(HomePurchase.property_location.asc(), HomePurchase.price_per_sqm.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_home_purchase = home_purchase_schema.dump(qry_res, many=True)
                    for result in dumped_home_purchase:
                        result['price_per_sqm'] = round(result['price_per_sqm'] * conversion, 2)
                    return dumped_home_purchase
                
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query = qry,
                    resource_for_url = 'cost_of_living.homepurchaselistresource',
                    key_name = 'home purchase data',   
                    schema = home_purchase_schema
                    )
                    dumped_home_purchase = pagination_helper.paginate_query()
                    for result in dumped_home_purchase['home purchase data']:
                        result['price_per_sqm'] = round(result['price_per_sqm'] * conversion, 2)
                    return dumped_home_purchase
            
            else:
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                    qry_res = qry.all()
                    dumped_home_purchase = home_purchase_schema.dump(qry_res, many=True)
                    return dumped_home_purchase
                
                qry_res = qry.all()
                pagination_helper = PaginationHelper(
                request,
                query=qry,
                resource_for_url='cost_of_living.homepurchaselistresource',
                key_name='home purchase data',   
                schema=home_purchase_schema
                )
                dumped_home_purchase = pagination_helper.paginate_query()
                return dumped_home_purchase
    
    # Creates a record for relevant purchasing costs of buying a property in a particular location
    def post(self):
        home_purchase_dict = request.get_json()

        if home_purchase_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                homepurchase_data = get_data(file_prefix='homepurchase')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new homepurchase rows added
            homepurchase_added = 0

            # Retrieve all locations
            locations = Location.query.all()

            print(len(homepurchase_data))

            for data in homepurchase_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location:
                    if not HomePurchase.is_unique(location_id=location.id, property_location=data['Property Location']):
                        continue
                    try:
                        home_purchase = HomePurchase(property_location=data['Property Location'], 
                        price_per_sqm=data['Price per Square Meter'], 
                        mortgage_interest=data['Mortgage Interest'],
                        location=location)
                        home_purchase.add(home_purchase)
                        homepurchase_added += 1

                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)

                else:
                    continue
                
            response = {'message': f'Successfully added {homepurchase_added} homepurchase records'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates homepurchase record
    def patch(self):
        
        homepurchase_dict = request.get_json(force = True)

        if homepurchase_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                homepurchase_data = get_data(file_prefix = 'homepurchase')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value

            # Track homepurchase rows updated
            homepurchase_updated = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in homepurchase_data:
                has_been_updated = False
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location != None:
                    try:
                        homepurchase = HomePurchase.query.filter_by(location_id=location.id, property_location=data['Property Location']).first()
                        if homepurchase == None:
                            continue
                        if data['Price per Square Meter'] != homepurchase.price_per_sqm:
                            homepurchase.price_per_sqm = data['Price per Square Meter']
                            has_been_updated = True
                        if data['Mortgage Interest'] != homepurchase.mortgage_interest:
                            homepurchase.mortgage_interest = data['Mortgage Interest']
                            has_been_updated = True
                        else:
                            continue
                
                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)
                
                if has_been_updated == True:
                    homepurchase_updated += 1
            
            response = {'message': f'Successfully updated {homepurchase_updated} homepurchase records'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class RentResource(Resource):
    # Retrieve rental costs from a specific id
    @swag_from('swagger/rentresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:
            rent = Rent.query.get_or_404(id)
            dumped_rent = rent_schema.dump(rent)
            return dumped_rent
    
    # Deletes Rent record
    def delete(self, id):
        admin_dict = request.get_json()
        rent = Rent.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                rent.delete(rent)
                response = {'message': 'Rent id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class RentListResource(Resource):
    # Retrieves rental costs from a specified country, city, abbreviation or combination of the 3 or all ids.
    @swag_from('swagger/rentlistresource_get.yml')
    def get(self):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:
            qry = orm.session.query(Rent).join(Location, Rent.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Rent.property_location.asc(), Rent.bedrooms.asc(), Rent.monthly_price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_rent = rent_schema.dump(qry_res, many=True)
                    for result in dumped_rent:
                        result['monthly_price'] = round(result['monthly_price'] * conversion,2)
                    return dumped_rent
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query=qry,
                    resource_for_url='cost_of_living.rentlistresource',
                    key_name='rental data',   
                    schema=rent_schema
                    )
                    dumped_rent = pagination_helper.paginate_query()
                    for result in dumped_rent['rental data']:
                        result['monthly_price'] = round(result['monthly_price'] * conversion,2)
                    return dumped_rent
            
            else:
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                    qry_res = qry.all()
                    dumped_rent = rent_schema.dump(qry_res, many=True)
                    return dumped_rent
                
                qry_res = qry.all()
                pagination_helper = PaginationHelper(
                request,
                query=qry,
                resource_for_url='cost_of_living.rentlistresource',
                key_name='rental data',   
                schema=rent_schema
                )
                dumped_rent = pagination_helper.paginate_query()
                return dumped_rent

    # Creates new rent records
    def post(self):
        rent_dict = request.get_json()

        if rent_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                rent_data = get_data(file_prefix='rent')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new rent rows added
            rent_added = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in rent_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location:
                    if not Rent.is_unique(location_id=location.id, property_location=data['Property Location'], bedrooms=data['Bedrooms']):
                        continue
                    try:
                        rent = Rent(property_location=data['Property Location'], 
                        bedrooms=data['Bedrooms'], 
                        monthly_price=data['Monthly Price'],
                        location=location)
                        rent.add(rent)
                        rent_added += 1

                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)

                else:
                    continue
                
            response = {'message': f'Successfully added {rent_added} rent records'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates monthly price for specified record
    def patch(self):
        
        rent_dict = request.get_json(force=True)

        if rent_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                rent_data = get_data(file_prefix='rent')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value

            # Track rent rows updated
            rent_updated = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in rent_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location != None:
                    try:
                        rent = Rent.query.filter_by(location_id=location.id, property_location=data['Property Location'], bedrooms=data['Bedrooms']).first()
                        if rent == None:
                            continue
                        elif data['Monthly Price'] != rent.monthly_price:
                            rent.monthly_price = data['Monthly Price']
                            rent_updated += 1
                        else:
                            continue
                    
                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)
            
            response = {'message': f'Successfully updated {rent_updated} rent records'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class UtilitiesResource(Resource):
    # Retrieve information regarding utility from a specific id
    @swag_from('swagger/utilitiesresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:
            utilities = Utilities.query.get_or_404(id)
            dumped_utilities = utilities_schema.dump(utilities)
            return dumped_utilities
    
    # Deletes Utilities record
    def delete(self, id):
        admin_dict = request.get_json()
        utilities = Utilities.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                utilities.delete(utilities)
                response = {'message': 'Utilities id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class UtilitiesListResource(Resource):
    # Retrieves information regarding a utility from a given country, city, abbreviation, combination of the 3 or all utilities.
    @swag_from('swagger/utilitieslistresource_get.yml')
    def get(self):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:
            qry = orm.session.query(Utilities).join(Location, Utilities.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Utilities.utility.asc(), Utilities.monthly_price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_utilities = utilities_schema.dump(qry_res, many=True)
                    for result in dumped_utilities:
                        result['monthly_price'] = round(result['monthly_price'] * conversion,2)
                    return dumped_utilities
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query=qry,
                    resource_for_url='cost_of_living.utilitieslistresource',
                    key_name='utilities',   
                    schema=utilities_schema
                    )
                    dumped_utilities = pagination_helper.paginate_query()
                    for result in dumped_utilities['utilities']:
                        result['monthly_price'] = round(result['monthly_price'] * conversion,2)
                    return dumped_utilities
            
            else:
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                    qry_res = qry.all()
                    dumped_utilities = utilities_schema.dump(qry_res, many=True)
                    return dumped_utilities
                
                qry_res = qry.all()
                pagination_helper = PaginationHelper(
                request,
                query=qry,
                resource_for_url='cost_of_living.utilitieslistresource',
                key_name='utilities',   
                schema=utilities_schema
                )
                dumped_utilities = pagination_helper.paginate_query()
                return dumped_utilities
    
    # Creates new utilities records
    def post(self):
        utilities_dict = request.get_json()

        if utilities_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                utilities_data = get_data(file_prefix='utilities')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new utilities rows added
            utilities_added = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in utilities_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location:
                    if not Utilities.is_unique(location_id=location.id, utility=data['Utility']):
                        continue
                    try:
                        utilities = Utilities(utility=data['Utility'], 
                        monthly_price=data['Monthly Price'],
                        location=location)
                        utilities.add(utilities)
                        utilities_added += 1

                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)

                else:
                    continue
                
            response = {'message': f'Successfully added {utilities_added} utilities records'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

    # Updates monthly price for specified record
    def patch(self):
        
        utilities_dict = request.get_json(force=True)

        if utilities_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                utilities_data = get_data(file_prefix='utilities')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value

            # Track utilities rows updated
            utilities_updated = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in utilities_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location != None:
                    try:
                        utilities = Utilities.query.filter_by(location_id=location.id, utility=data['Utility']).first()
                        if utilities == None:
                            continue
                        elif data['Monthly Price'] != utilities.monthly_price:
                            utilities.monthly_price = data['Monthly Price']
                            utilities_updated +=1
                        else:
                            continue
                    
                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)
            
            response = {'message': f'Successfully updated {utilities_updated} utilities records'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value   

class TransportationResource(Resource):
    # Retrieves information regarding mode of transport from a specific id
    @swag_from('swagger/transportationresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:  
            transportation = Transportation.query.get_or_404(id)
            dumped_transportation = transportation_schema.dump(transportation)
            return dumped_transportation
    
    # Deletes Transportation record
    def delete(self, id):
        admin_dict = request.get_json()
        transportation = Transportation.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                transportation.delete(transportation)
                response = {'message': 'Transportation id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class TransportationListResource(Resource):
    # Retrieves information for a particular mode of transport from a particular country, city, abbreviation, combination of the 3 or all modes of transport.
    @swag_from('swagger/transportationlistresource_get.yml')
    def get(self):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:    
            qry = orm.session.query(Transportation).join(Location, Transportation.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Transportation.type.asc(), Transportation.price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_transportation = transportation_schema.dump(qry_res, many=True)
                    for result in dumped_transportation:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_transportation
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query=qry,
                    resource_for_url='cost_of_living.transportationlistresource',
                    key_name='transportation data',   
                    schema=transportation_schema
                    )
                    dumped_transportation = pagination_helper.paginate_query()
                    for result in dumped_transportation['transportation data']:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_transportation
            
            else:
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                    qry_res = qry.all()
                    dumped_transportation = transportation_schema.dump(qry_res, many=True)
                    return dumped_transportation
                
                qry_res=qry.all()
                pagination_helper = PaginationHelper(
                request,
                query=qry,
                resource_for_url='cost_of_living.transportationlistresource',
                key_name='transportation data',   
                schema=transportation_schema
                )
                dumped_transportation = pagination_helper.paginate_query()
                return dumped_transportation
    
    # Creates a new transportation record
    def post(self):
        transportation_dict = request.get_json()

        if transportation_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                transportation_data = get_data(file_prefix='transportation')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new transportation rows added
            transportation_added = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in transportation_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location:
                    if not Transportation.is_unique(location_id=location.id, type=data['Type']):
                        continue
                    try:
                        transportation = Transportation(type=data['Type'], 
                        price=data['Price'],
                        location=location)
                        transportation.add(transportation)
                        transportation_added += 1

                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)

                else:
                    continue
                
            response = {'message': f'Successfully added {transportation_added} transportation records'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates price for specified record
    def patch(self):
        
        transportation_dict = request.get_json(force=True)

        if transportation_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                transportation_data = get_data(file_prefix='transportation')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value

            # Track transportation updated
            transportation_updated = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in transportation_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location != None:
                    try:
                        transportation = Transportation.query.filter_by(location_id=location.id, type=data['Type']).first()
                        if transportation == None:
                            continue
                        elif data['Price'] != transportation.price:
                            transportation.price = data['Price']
                            transportation_updated += 1
                        else:
                            continue
                    
                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)
            
            response = {'message': f'Successfully updated {transportation_updated} transportation records'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value   

class FoodBeverageResource(Resource):
    # Retrieves information regarding a food and beverage item from a specific id
    @swag_from('swagger/foodbeverageresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:
            if id != None:
                food_and_beverage = FoodBeverage.query.get_or_404(id)
                dumped_food_and_beverage = foodbeverage_schema.dump(food_and_beverage)
                return dumped_food_and_beverage
    
    # Deletes FoodBeverage record
    def delete(self, id):
        admin_dict = request.get_json()
        food_and_beverage = FoodBeverage.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                food_and_beverage.delete(food_and_beverage)
                response = {'message': 'FoodBeverage id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class FoodBeverageListResource(Resource):
    @swag_from('swagger/foodbeveragelistresource_get.yml')
    # Retrieves information regarding a food and beverage item from a particular country, city, abbreviation, combination of the 3 or all items.
    def get(self):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:
            qry = orm.session.query(FoodBeverage).join(Location, FoodBeverage.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(FoodBeverage.item_category.asc(), FoodBeverage.purchase_point.asc(), FoodBeverage.item.asc(),
            FoodBeverage.price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_food_and_beverage = foodbeverage_schema.dump(qry_res, many=True)
                    for result in dumped_food_and_beverage:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_food_and_beverage
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query=qry,
                    resource_for_url='cost_of_living.foodbeveragelistresource',
                    key_name='food and beverage data',   
                    schema=foodbeverage_schema
                    )
                    dumped_food_and_beverage = pagination_helper.paginate_query()
                    for result in dumped_food_and_beverage['food and beverage data']:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_food_and_beverage
            
            else:
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry= qry.filter(Location.city == city)
                    qry_res = qry.all()
                    dumped_food_and_beverage = foodbeverage_schema.dump(qry_res, many=True)
                    return dumped_food_and_beverage
                
                qry_res = qry.all()
                pagination_helper = PaginationHelper(
                request,
                query=qry,
                resource_for_url='cost_of_living.foodbeveragelistresource',
                key_name='food and beverage data',   
                schema=foodbeverage_schema
                )
                dumped_food_and_beverage = pagination_helper.paginate_query()
                return dumped_food_and_beverage
    
    # Creates a new foodbeverage record
    def post(self):
        foodbeverage_dict = request.get_json()

        if foodbeverage_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                foodbeverage_data = get_data(file_prefix='foodbeverage')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new foodbeverage rows added
            foodbeverage_added = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in foodbeverage_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location:
                    if not FoodBeverage.is_unique(location_id=location.id, item_category=data['Item Category'],
                    purchase_point=data['Purchase Point'], item=data['Item']):
                        continue
                    try:
                        foodbeverage = FoodBeverage(item_category=data['Item Category'], 
                        purchase_point=data['Purchase Point'],
                        item=data['Item'],
                        price=data['Price'],
                        location=location)
                        foodbeverage.add(foodbeverage)
                        foodbeverage_added += 1

                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)

                else:
                    continue
                
            response = {'message': f'Successfully added {foodbeverage_added} foodbeverage records'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates price for specified record
    def patch(self):
        
        foodbeverage_dict = request.get_json(force=True)

        if foodbeverage_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                foodbeverage_data = get_data(file_prefix='foodbeverage')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value

            # Track foodbeverage updated
            foodbeverage_updated = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in foodbeverage_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location != None:
                    try:
                        foodbeverage = FoodBeverage.query.filter_by(location_id=location.id, item_category=data['Item Category'],
                        purchase_point=data['Purchase Point'], item=data['Item']).first()
                        if foodbeverage == None:
                            continue
                        elif data['Price'] != foodbeverage.price:
                            foodbeverage.price = data['Price']
                            foodbeverage_updated += 1
                        else:
                            continue
                    
                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)
            
            response = {'message': f'Successfully updated {foodbeverage_updated} foodbeverage records'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class ChildcareResource(Resource):
    # Retrieves information regarding childcare service from a specific id
    @swag_from('swagger/childcareresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:
            childcare = Childcare.query.get_or_404(id)
            dumped_childcare = childcare_schema.dump(childcare)
            return dumped_childcare
    
    # Deletes Childcare record
    def delete(self, id):
        admin_dict = request.get_json()
        childcare = Childcare.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                childcare.delete(childcare)
                response = {'message': 'Childcare id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class ChildcareListResource(Resource):
    # Retrives information regarding childcare service from a given country, city, abbreviation, combination of the 3 or all services.
    @swag_from('swagger/childcarelistresource_get.yml')
    def get(self):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:
            qry = orm.session.query(Childcare).join(Location, Childcare.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Childcare.type.asc(), Childcare.annual_price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_childcare = childcare_schema.dump(qry_res, many=True)
                    for result in dumped_childcare:
                        result['annual_price'] = round(result['annual_price'] * conversion,2)
                    return dumped_childcare
            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query=qry,
                    resource_for_url='cost_of_living.childcarelistresource',
                    key_name='childcare data',   
                    schema=childcare_schema
                    )
                    dumped_childcare = pagination_helper.paginate_query()
                    for result in dumped_childcare['childcare data']:
                        result['annual_price'] = round(result['annual_price'] * conversion,2)
                    return dumped_childcare
            
            else:
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                    qry_res = qry.all()
                    dumped_childcare = childcare_schema.dump(qry_res, many=True)
                    return dumped_childcare
                
                qry_res = qry.all()
                pagination_helper = PaginationHelper(
                request,
                query=qry,
                resource_for_url='cost_of_living.childcarelistresource',
                key_name='childcare data',   
                schema=childcare_schema
                )
                dumped_childcare = pagination_helper.paginate_query()
                return dumped_childcare
    
    # Creates a new childcare record
    def post(self):
        childcare_dict = request.get_json()

        if childcare_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                childcare_data = get_data(file_prefix='childcare')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new childcare rows added
            childcare_added = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in childcare_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location:
                    if not Childcare.is_unique(location_id=location.id, type=data['Type']):
                        continue
                    try:
                        childcare = Childcare(type=data['Type'], 
                        annual_price=data['Annual Price'],
                        location=location)
                        childcare.add(childcare)
                        childcare_added += 1

                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)

                else:
                    continue
                
            response = {'message': f'Successfully added {childcare_added} childcare records'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates annual price for specified record
    def patch(self):
        
        childcare_dict = request.get_json(force=True)

        if childcare_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                childcare_data = get_data(file_prefix='childcare')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track childcare updated
            childcare_updated = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in childcare_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)
                
                if location != None:
                    try:
                        childcare = Childcare.query.filter_by(location_id=location.id, type=data['Type']).first()
                        if childcare == None:
                            continue
                        elif data['Annual Price'] != childcare.annual_price:
                            childcare.annual_price = data['Annual Price']
                            childcare_updated += 1
                        else:
                            continue
                    
                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)
            
            response = {'message': f'Successfully updated {childcare_updated} childcare records'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class ApparelResource(Resource):
    # Retrieves apparel information from a specific id
    @swag_from('swagger/apparelresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:
            apparel = Apparel.query.get_or_404(id)
            dumped_apparel = apparel_schema.dump(apparel)
            return dumped_apparel

    # Deletes Apparel record
    def delete(self, id):
        admin_dict = request.get_json()
        apparel = Apparel.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                apparel.delete(apparel)
                response = {'message': 'Apparel id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class ApparelListResource(Resource):
    # Retrieves information for a given apparel item from a particular country, city, abbreviation, combination of the 3 or all items.
    @swag_from('swagger/apparellistresource_get.yml')
    def get(self):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:
            qry = orm.session.query(Apparel).join(Location, Apparel.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Apparel.item.asc(), Apparel.price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_apparel = apparel_schema.dump(qry_res, many=True)
                    for result in dumped_apparel:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_apparel            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query=qry,
                    resource_for_url='cost_of_living.apparellistresource',
                    key_name='apparel data',   
                    schema=apparel_schema
                    )
                    dumped_apparel = pagination_helper.paginate_query()
                    for result in dumped_apparel['apparel data']:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_apparel
            
            else:
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                    qry_res = qry.all()
                    dumped_apparel = apparel_schema.dump(qry_res, many=True)
                    return dumped_apparel
                
                qry_res = qry.all()
                pagination_helper = PaginationHelper(
                request,
                query=qry,
                resource_for_url='cost_of_living.apparellistresource',
                key_name='apparel data',   
                schema=apparel_schema
                )
                dumped_apparel = pagination_helper.paginate_query()
                return dumped_apparel
    
    # Creates a new apparel record
    def post(self):
        apparel_dict = request.get_json()

        if apparel_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                apparel_data = get_data(file_prefix = 'apparel')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new apparel rows added
            apparel_added = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in apparel_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location:
                    if not Apparel.is_unique(location_id=location.id, item=data['Item']):
                        continue
                    try:
                        apparel = Apparel(item=data['Item'], 
                        price=data['Price'],
                        location=location)
                        apparel.add(apparel)
                        apparel_added += 1

                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)

                else:
                    continue
                
            response = {'message': f'Successfully added {apparel_added} apparel records'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates annual price for specified record
    def patch(self):
        
        apparel_dict = request.get_json(force=True)

        if apparel_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                apparel_data = get_data(file_prefix='apparel')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value

            # Track apparel updated
            apparel_updated = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in apparel_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location != None:
                    try:
                        apparel = Apparel.query.filter_by(location_id=location.id, item=data['Item']).first()
                        if apparel == None:
                            continue
                        elif data['Price'] != apparel.price:
                            apparel.price = data['Price']
                            apparel_updated += 1
                        else:
                            continue
                    
                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)
            
            response = {'message': f'Successfully updated {apparel_updated} apparel records'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class LeisureResource(Resource):
    # Retrieves information for a leisure activity from a specified id
    @swag_from('swagger/leisureresource_get.yml')
    def get(self, id):
        if authenticate_jwt() == True:
            leisure = Leisure.query.get_or_404(id)
            dumped_leisure = leisure_schema.dump(leisure)
            return dumped_leisure
    
    # Deletes Leisure record
    def delete(self, id):
        admin_dict = request.get_json()
        leisure = Leisure.query.get_or_404(id)

        if admin_dict.get('admin') == os.environ.get('ADMIN_KEY'):
        
            try:
                leisure.delete(leisure)
                response = {'message': 'Leisure id successfully deleted'}
                return response
            
            except SQLAlchemyError as e:
                sql_alchemy_error_response(e)
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

class LeisureListResource(Resource):
    # Retrieves information for a given leisure acitivty from a given country, city, abbreviation, combination of the three or all activities.
    @swag_from('swagger/leisurelistresource_get.yml')
    def get(self):
        country = request.args.get('country')
        city = request.args.get('city')
        abbreviation = request.args.get('abbreviation')

        if authenticate_jwt() == True:
            qry = orm.session.query(Leisure).join(Location, Leisure.location_id == Location.id)\
            .join(Currency, Location.currency_id == Currency.id).order_by(Leisure.activity.asc(), Leisure.price.asc())
        
            if abbreviation:

                conversion = orm.session.query(Currency.usd_to_local_exchange_rate).join(Location, Location.currency_id == Currency.id).filter(Currency.abbreviation == abbreviation).first()[0]
            
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                
                if (city and not country) or (city and country):
                    qry_res = qry.all()
                    dumped_leisure = leisure_schema.dump(qry_res, many = True)
                    for result in dumped_leisure:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_leisure            
                else:
                    pagination_helper = PaginationHelper(
                    request,
                    query=qry,
                    resource_for_url='cost_of_living.leisurelistresource',
                    key_name='leisure data',   
                    schema=leisure_schema
                    )
                    dumped_leisure = pagination_helper.paginate_query()
                    for result in dumped_leisure['leisure data']:
                        result['price'] = round(result['price'] * conversion,2)
                    return dumped_leisure
            
            else:
                if country:
                    qry = qry.filter(Location.country == country)
                if city:
                    qry = qry.filter(Location.city == city)
                    qry_res = qry.all()
                    dumped_leisure = leisure_schema.dump(qry_res, many=True)
                    return dumped_leisure
                
                qry_res = qry.all()
                pagination_helper = PaginationHelper(
                request,
                query=qry,
                resource_for_url='cost_of_living.leisurelistresource',
                key_name='leisure data',   
                schema=leisure_schema
                )
                dumped_leisure = pagination_helper.paginate_query()
                return dumped_leisure
    
    # Creates a new leisure record
    def post(self):
        leisure_dict = request.get_json()

        if leisure_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                leisure_data = get_data(file_prefix='leisure')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value
            
            # Track new leisure rows added
            leisure_added = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in leisure_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location:
                    if not Leisure.is_unique(location_id=location.id, activity=data['Activity']):
                        continue
                    try:
                        leisure = Leisure(activity=data['Activity'], 
                        price=data['Price'],
                        location=location)
                        leisure.add(leisure)
                        leisure_added += 1

                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)

                else:
                    continue
            response = {'message': f'Successfully added {leisure_added} leisure records'}
            return response, HttpStatus.created_201.value
        
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value
    
    # Updates annual price for specified record
    def patch(self):
        
        leisure_dict = request.get_json(force = True)

        if leisure_dict.get('admin') == os.environ.get('ADMIN_KEY'):
            try:
                leisure_data = get_data(file_prefix='leisure')
            except botocore.exceptions.ClientError as e:
                response = {'message': e}
                return response, HttpStatus.notfound_404.value

            # Track apparel updated
            leisure_updated = 0

            # Retrieve all locations
            locations = Location.query.all()

            for data in leisure_data:
                location_city = data['City']
                location = next((loc for loc in locations if loc.city == location_city), None)

                if location != None:
                    try:
                        leisure = Leisure.query.filter_by(location_id=location.id, activity=data['Activity']).first()
                        if leisure == None:
                            continue
                        elif data['Price'] != leisure.price:
                            leisure.price = data['Price']
                            leisure_updated += 1
                        else:
                            continue
                    
                    except SQLAlchemyError as e:
                        sql_alchemy_error_response(e)
            
            response = {'message': f'Successfully updated {leisure_updated} leisure records'}
            return response, HttpStatus.ok_200.value
        else:
            response = {'message': 'Admin privileges needed'}
            return response, HttpStatus.forbidden_403.value

cost_of_living.add_resource(UserResource, '/auth/user')
cost_of_living.add_resource(LoginResource, '/auth/login')
cost_of_living.add_resource(LogoutResource, '/auth/logout')
cost_of_living.add_resource(ResetPasswordResource, '/auth/user/password_reset')
cost_of_living.add_resource(CurrencyResource, '/currencies/<int:id>')        
cost_of_living.add_resource(CurrencyListResource, '/currencies')
cost_of_living.add_resource(LocationResource, '/locations/<int:id>')
cost_of_living.add_resource(LocationListResource, '/locations')
cost_of_living.add_resource(HomePurchaseResource, '/homepurchase/<int:id>')
cost_of_living.add_resource(HomePurchaseListResource, '/homepurchase')
cost_of_living.add_resource(RentResource, '/rent/<int:id>')
cost_of_living.add_resource(RentListResource, '/rent')
cost_of_living.add_resource(UtilitiesResource, '/utilities/<int:id>')
cost_of_living.add_resource(UtilitiesListResource, '/utilities')
cost_of_living.add_resource(TransportationResource, '/transportation/<int:id>')
cost_of_living.add_resource(TransportationListResource, '/transportation')
cost_of_living.add_resource(FoodBeverageResource, '/foodbeverage/<int:id>')
cost_of_living.add_resource(FoodBeverageListResource, '/foodbeverage')
cost_of_living.add_resource(ChildcareResource, '/childcare/<int:id>')
cost_of_living.add_resource(ChildcareListResource, '/childcare')
cost_of_living.add_resource(ApparelResource, '/apparel/<int:id>')
cost_of_living.add_resource(ApparelListResource, '/apparel')
cost_of_living.add_resource(LeisureResource, '/leisure/<int:id>')
cost_of_living.add_resource(LeisureListResource, '/leisure')
