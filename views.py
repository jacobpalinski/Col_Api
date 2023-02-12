from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required
from httpstatus import HttpStatus
from models import (User,UserSchema,BlacklistToken,Currency,CurrencySchema,Location,LocationSchema,
Home_Purchase,Home_PurchaseSchema,Rent,RentSchema,Utilities,UtilitiesSchema,
Transportation,TransportationSchema,Food_and_Beverage, Food_and_BeverageSchema,
Childcare,ChildcareSchema,Apparel, ApparelSchema, Leisure,LeisureSchema)
from helpers import *
from sqlalchemy.exc import SQLAlchemyError

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
    @jwt_required
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
                    'creation_date': user.creation_date
                    }
                }
                return response, HttpStatus.ok_200.value
            response = {'message': resp}
            return response, HttpStatus.unauthorized_401.value
        else:
            response = {'message' : 'Provide a valid auth token'}
            return response, HttpStatus.forbidden_403.value
                
    def post(self):
        user_register_dict = request.get_json()
        request_not_empty(user_register_dict)
        validate_request(user_schema,user_register_dict)

        user = User.query.filter_by(email = user_register_dict['email']).first()
        if not user:
            try:
                user = User(email = user_register_dict['email'])
                user.check_password_strength_and_hash_if_ok(user_register_dict['password'])
                user.add(user)
                response = {'message': 'successfully registered'}
                return response, HttpStatus.created_201.value

            except Exception as e:
                response = {'message' : 'Error. Please try again'}
                return response, HttpStatus.unauthorized_401.value
        
        else:
            response = {'message' : 'User already exists. Please log in'}
            return response, HttpStatus.conflict_409.value

class LoginResource(Resource):
    def post(self):
        user_dict = request.get_json()
        request_not_empty(user_dict)
        validate_request(user_schema,user_dict)

        try:
            user = User.query.filter_by(email = user_dict['email']).first()
            if user.verify_password(user_dict['password']):
                auth_token = user.encode_auth_token(user.id)
                if auth_token:
                    response = {
                    'message': 'successfully logged in.',
                    'auth_token': auth_token.decode()}
                    return response, HttpStatus.ok_200.value
            else:
                response = {'message': 'User does not exist.'}
                return response, HttpStatus.notfound_404
        
        except Exception as e:
            print(e)
            response = {'message': 'Try again'}
            return response, HttpStatus.internal_server_error.value

class LogoutResource(Resource):
    @jwt_required
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
            response = {'message' : 'Provide a valid auth token.'}
            return response, HttpStatus.forbidden_403.value

class ResetPasswordResource(Resource):
    def post(self):
        reset_password_dict = request.get_json()
        request_not_empty(reset_password_dict)
        validate_request(user_schema,reset_password_dict)
        
        try:
            user = User.query.filter_by(email = reset_password_dict['email']).first()
            if user:
                user.check_password_strength_and_hash_if_ok(reset_password_dict['password_hash'])
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
    @jwt_required
    def get(self,id=None):

        if id != None:
            currency = Currency.query.get_or_404(id)
            dumped_currency = currency_schema.dump(currency)
            return dumped_currency
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Currency.query.all(),
                resource_for_url = 'cost_of_living.currencyresource',
                key_name = 'results',
                schema = currency_schema
            )
            paginated_currencies = pagination_helper.paginate_query()
            return paginated_currencies
    
    def post(self):
        currency_dict = request.get_json()
        request_not_empty(currency_dict)
        validate_request(currency_schema,currency_dict)

        try:
            currency = Currency(abbreviation = currency_dict['abbreviation'],
            usd_to_local_exchange_rate = currency_dict['usd_to_local_exchange_rate'])
            currency.add(currency)
            query = Currency.query.get(currency.id)
            dump_result = currency_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def patch(self,id):
        currency = Currency.query.get_or_404(id)
        
        currency_dict = request.get_json(force = True)
        request_not_empty(currency_dict)
        validate_request(currency_schema,currency_dict)

        try:
            if 'abbreviation' in currency_dict and currency_dict['abbreviation'] != None:
                currency.abbreviation = currency_dict['abbreviation']
            if 'usd_to_local_exchange_rate' in currency_dict and \
            currency_dict['usd_to_local_exchange_rate'] != None:
                currency.usd_to_local_exchange_rate = currency_dict['usd_to_local_exchange_rate']
        
            currency.update()
            self.get(id)

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def delete(self,id):
        currency = Currency.query.get_or_404(id)
        
        try:
            delete_object(currency)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)

class LocationListResource(Resource):
    @jwt_required
    def get(self,id):

        if id != None:
            location = Location.query.get_or_404(id)
            dumped_location = location_schema.dump(location)
            return dumped_location

        else:
            pagination_helper = PaginationHelper(
                request,
                query = Location.query.all(),
                resource_for_url = 'cost_of_living.locationlistesource',
                key_name = 'results',
                schema = location_schema
            )
            paginated_locations = pagination_helper.paginate_query()
            return paginated_locations
    
    def post(self):
        location_dict = request.get_json()
        request_not_empty(location_dict)
        validate_request(location_schema,location_dict)
        
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
    
    def delete(self,id):
        location = Location.query.get_or_404(id)
        
        try:
            delete_object(location)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)

class HomePurchaseResource(Resource):
    @jwt_required
    def get(self,id=None,country=None,city=None,abbreviation=None):

        if id != None:
            home_purchase = Home_Purchase.query.get_or_404(id)
            dumped_home_purchase = home_purchase_schema.dump(home_purchase)
            return dumped_home_purchase

        elif None not in (country,city,abbreviation):
            home_purchase = Home_Purchase.query(Home_Purchase.id,
            Home_Purchase.property_location, 
            (Home_Purchase.price_per_sqm * Currency.usd_to_local_exchange_rate).label("price_per_sqm"),
            Home_Purchase.mortgage_interest,
            Home_Purchase.location_id).join(Location, Home_Purchase.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Home_Purchase.property_location.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase,many=True)
            return dumped_home_purchase    
        
        elif  None not in (country,city) and abbreviation == None:
            home_purchase = Home_Purchase.query.join(Location, 
            Home_Purchase.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Home_Purchase.property_location.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase,many=True)
            return dumped_home_purchase
        
        elif country != None and None in (city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Home_Purchase.query.join(Location, 
                Home_Purchase.location_id == Location.id).filter(Location.country == country)\
                .order_by(Home_Purchase.property_location.asc(), Home_Purchase.price_per_sqm.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.homepurchaseresource',
                key_name = 'results',
                schema = home_purchase_schema
            )
            paginated_home_purchase = pagination_helper.paginate_query()
            return paginated_home_purchase
        
        elif None in (country,city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Home_Purchase.query.join(Location, 
                Home_Purchase.location_id == Location.id)\
                .order_by(Home_Purchase.property_location.asc(), Home_Purchase.price_per_sqm.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.homepurchaseresource',
                key_name = 'results',
                schema = home_purchase_schema
            )
            paginated_home_purchase = pagination_helper.paginate_query()
            return paginated_home_purchase
        
        elif city != None and None in (country,abbreviation):
            home_purchase = Home_Purchase.query.join(Location, 
            Home_Purchase.location_id == Location.id).filter(Location.city == city)\
            .order_by(Home_Purchase.property_location.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase,many = True)
            return dumped_home_purchase
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Home_Purchase.query(Home_Purchase.id,
                Home_Purchase.property_location, 
                (Home_Purchase.price_per_sqm * Currency.usd_to_local_exchange_rate).label("price_per_sqm"),
                Home_Purchase.mortgage_interest,
                Home_Purchase.location_id).join(Location, Home_Purchase.location_id == Location.id)\
                .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
                .order_by(Home_Purchase.property_location.asc(),Home_Purchase.price_per_sqm.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.homepurchaseresource',
                key_name = 'results',
                schema = home_purchase_schema
            )
 
    def post(self):
        home_purchase_dict = request.get_json()
        request_not_empty(home_purchase_dict)
        validate_request(home_purchase_schema,home_purchase_dict)
        
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
    
    def patch(self,id):
        home_purchase = Home_Purchase.query.get_or_404(id)
        
        home_purchase_dict = request.get_json(force = True)
        request_not_empty(home_purchase_dict)
        validate_request(home_purchase_schema,home_purchase_dict)

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

    def delete(self,id):
        home_purchase = Home_Purchase.query.get_or_404(id)
        
        try:
            delete_object(home_purchase)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)

class RentResource(Resource):
    @jwt_required
    def get(self,id=None,country=None,city=None,abbreviation=None):

        if id != None:
            rent = Rent.query.get_or_404(id)
            dumped_rent = rent_schema.dump(rent)
            return dumped_rent

        elif None not in (country,city,abbreviation):
            rent = Rent.query(Rent.id, Rent.property_location,Rent.bedrooms,
            (Rent.monthly_price * Currency.usd_to_local_exchange_rate).label("monthly_price"),
            Rent.location_id).join(Location, Rent.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Rent.bedrooms.asc()).all().get_or_404()
            dumped_rent = rent_schema.dump(rent._asdict(),many = True)
            return dumped_rent
        
        elif  None not in (country,city) and abbreviation == None:
            rent = Rent.query.join(Location, 
            Rent.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Rent.bedrooms.asc()).all().get_or_404()
            dumped_rent = rent_schema.dump(rent,many = True)
            return dumped_rent
        
        elif country != None and None in (city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Rent.query.join(Location, 
                Rent.location_id == Location.id).filter(Location.country == country)\
                .order_by(Rent.bedrooms.asc(), Rent.monthly_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.rentresource',
                key_name = 'results',
                schema = rent_schema
            )
            paginated_rent = pagination_helper.paginate_query()
            return paginated_rent
        
        elif None in (country,city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Rent.query.join(Location, 
                Rent.location_id == Location.id)\
                .order_by(Rent.bedrooms.asc(), Rent.monthly_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.rentresource',
                key_name = 'results',
                schema = rent_schema
            )
            paginated_rent = pagination_helper.paginate_query()
            return paginated_rent
        
        elif city != None and None in (country,abbreviation):
            rent = Rent.query.join(Location, 
            Rent.location_id == Location.id).filter(Location.city == city)\
            .order_by(Rent.bedrooms.asc()).all().get_or_404()
            dumped_rent = rent_schema.dump(rent,many = True)
            return dumped_rent
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Rent.query(Rent.id, Rent.property_location,Rent.bedrooms,
                (Rent.monthly_price * Currency.usd_to_local_exchange_rate).label("monthly_price"),
                Rent.location_id).join(Location, Rent.location_id == Location.id)\
                .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
                .order_by(Rent.bedrooms.asc(),Rent.monthly_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.rentresource',
                key_name = 'results',
                schema = rent_schema
            )
            paginated_rent = pagination_helper.paginate_query()
            return paginated_rent

    def post(self):
        rent_dict = request.get_json()
        request_not_empty(rent_dict)
        validate_request(rent_schema,rent_dict)
        
        try:
            location_city = rent_dict['location']['city']
            location = Location.query.filter_by(city = location_city).first()

            if location is None:
                response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            rent = Rent(property_location = rent_dict['property_location'], 
            bedrooms = rent_dict['bedrooms'], monthly_price = rent_dict['monthly_price'])
            rent.add(rent)
            query = Rent.query.get(rent.id)
            dump_result = rent_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def patch(self,id):
        rent = Rent.query.get_or_404(id)
        
        rent_dict = request.get_json(force = True)
        request_not_empty(rent_dict)
        validate_request(rent_schema,rent_dict)

        try:
            if 'property_location' in rent_dict and rent_dict['property_location'] != None:
                rent.property_location = rent_dict['property_location']
            if 'price_per_sqm' in rent_dict and \
            rent_dict['bedrooms'] != None:
                rent.bedrooms = rent_dict['bedrooms']
            if 'monthly_price' in rent_dict and \
            rent_dict['monthly_price'] != None:
                rent.monthly_price = rent_dict['monthly_price']
        
            rent.update()
            self.get(id)

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def delete(self,id):
        rent = Rent.query.get_or_404(id)
        
        try:
            delete_object(rent)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)

class UtilitiesResource(Resource):
    @jwt_required
    def get(self,id=None,country=None,city=None,abbreviation=None):

        if id != None:
            utilities = Utilities.query.get_or_404(id)
            dumped_utilities = utilities_schema.dump(utilities)
            return dumped_utilities

        elif None not in (country,city,abbreviation):
            utilities = Utilities.query(Utilities.id,Utilities.utility,
            (Utilities.monthly_price * Currency.usd_to_local_exchange_rate).label("monthly_price"),
            Utilities.location_id).join(Location, 
            Utilities.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Utilities.utility.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities._asdict(),many = True)
            return dumped_utilities
        
        elif  None not in (country,city) and abbreviation == None:
            utilities = Utilities.query.join(Location, 
            Utilities.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Utilities.utility.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities,many = True)
            return dumped_utilities
        
        elif country != None and None in (city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Utilities.query.join(Location, 
                Utilities.location_id == Location.id).filter(Location.country == country)\
                .order_by(Utilities.utility.asc(), Utilities.monthly_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.utilitiesresource',
                key_name = 'results',
                schema = utilities_schema
            )
            paginated_utilities = pagination_helper.paginate_query()
            return paginated_utilities
        
        elif None in (country,city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Utilities.query.join(Location, 
                Utilities.location_id == Location.id)\
                .order_by(Utilities.utility.asc(), Utilities.monthly_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.utilitiesresource',
                key_name = 'results',
                schema = utilities_schema
            )
            paginated_utilities = pagination_helper.paginate_query()
            return paginated_utilities
        
        elif city != None and None in (country,abbreviation):
            utilities = Utilities.query.join(Location, 
            Utilities.location_id == Location.id).filter(Location.city == city)\
            .order_by(Utilities.utility.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities,many = True)
            return dumped_utilities
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Utilities.query(Utilities.id,Utilities.utility,
                (Utilities.monthly_price * Currency.usd_to_local_exchange_rate).label("monthly_price"),
                Utilities.location_id).join(Location, 
                Utilities.location_id == Location.id).join(Location, 
                Utilities.location_id == Location.id)\
                .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
                .order_by(Utilities.utility.asc(),Utilities.monthly_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.utilitiesresource',
                key_name = 'results',
                schema = utilities_schema
            )
            paginated_utilities = pagination_helper.paginate_query()
            return paginated_utilities
    
    def post(self):
        utilities_dict = request.get_json()
        request_not_empty(utilities_dict)
        validate_request(utilities_schema,utilities_dict)
        
        try:
            location_city = utilities_dict['location']['city']
            location = Location.query.filter_by(city = location_city).first()

            if location is None:
                response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            utilities = Utilities(utility = utilities_dict['utility'], 
            monthly_price = utilities_dict['monthly_price'])
            utilities.add(utilities)
            query = Utilities.query.get(utilities.id)
            dump_result = utilities_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def patch(self,id):
        utilities = Utilities.query.get_or_404(id)
        
        utilities_dict = request.get_json(force = True)
        request_not_empty(utilities_dict)
        validate_request(utilities_schema,utilities_dict)

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
    
    def delete(self,id):
        utilities = Utilities.query.get_or_404(id)
        
        try:
            delete_object(utilities)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)


class TransportationResource(Resource):
    @jwt_required
    def get(self,id=None,country=None,city=None,abbreviation=None):

        if id != None:
            transportation = Transportation.query.get_or_404(id)
            dumped_transportation = transportation_schema.dump(transportation)
            return dumped_transportation

        elif None not in (country,city,abbreviation):
            transportation = Transportation.query(Transportation.id,Transportation.type,
            (Transportation.price * Currency.usd_to_local_exchange_rate).label("price"),
            Transportation.location_id).join(Location, Transportation.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Transportation.type.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation._asdict(),many = True)
            return dumped_transportation
        
        elif  None not in (country,city) and abbreviation == None:
            transportation = Transportation.query.join(Location, 
            Transportation.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Transportation.type.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation,many = True)
            return dumped_transportation
        
        elif country != None and None in (city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Transportation.query.join(Location, 
                Transportation.location_id == Location.id).filter(Location.country == country)\
                .order_by(Transportation.type.asc(), Transportation.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.transportationresource',
                key_name = 'results',
                schema = transportation_schema
            )
            paginated_transportation = pagination_helper.paginate_query()
            return paginated_transportation
        
        elif None in (country,city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Transportation.query.join(Location, 
                Transportation.location_id == Location.id)\
                .order_by(Transportation.type.asc(), Transportation.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.transportationresource',
                key_name = 'results',
                schema = transportation_schema
            )
            paginated_transportation = pagination_helper.paginate_query()
            return paginated_transportation
        
        elif city != None and None in (country,abbreviation):
            transportation = Transportation.query.join(Location, 
            Transportation.location_id == Location.id).filter(Location.city == city)\
            .order_by(Transportation.type.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation,many = True)
            return dumped_transportation
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Transportation.query(Transportation.id,Transportation.type,
                (Transportation.price * Currency.usd_to_local_exchange_rate).label("price"),
                Transportation.location_id).join(Location, Transportation.location_id == Location.id)\
                .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
                .order_by(Transportation.type.asc(),Transportation.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.transportationresource',
                key_name = 'results',
                schema = transportation_schema
            )
            paginated_transportation = pagination_helper.paginate_query()
            return paginated_transportation
    
    def post(self):
        transportation_dict = request.get_json()
        request_not_empty(transportation_dict)
        validate_request(transportation_schema,transportation_dict)
        
        try:
            location_city = transportation_dict['location']['city']
            location = Location.query.filter_by(city = location_city).first()

            if location is None:
                response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            transportation = Transportation(type = transportation_dict['price'], 
            price = transportation_dict['monthly_price'])
            transportation.add(transportation)
            query = Transportation.query.get(transportation.id)
            dump_result = transportation_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def patch(self,id):
        transportation = Transportation.query.get_or_404(id)
        
        transportation_dict = request.get_json(force = True)
        request_not_empty(transportation_dict)
        validate_request(transportation_schema,transportation_dict)

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
    
    def delete(self,id):
        transportation = Transportation.query.get_or_404(id)
        
        try:
            delete_object(transportation)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)

class FoodBeverageResource(Resource):
    @jwt_required
    def get(self,id=None,country=None,city=None,abbreviation=None):

        if id != None:
            food_and_beverage = Food_and_Beverage.query.get_or_404(id)
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage)
            return dumped_food_and_beverage

        elif None not in (country,city,abbreviation):
            food_and_beverage = Food_and_Beverage.query(Food_and_Beverage.id,
            Food_and_Beverage.item_category,Food_and_Beverage.purchase_point,
            Food_and_Beverage.item,
            (Food_and_Beverage.price * Currency.usd_to_local_exchange_rate).label("price"),
            Food_and_Beverage.location_id).join(Location, Food_and_Beverage.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage._asdict(),many = True)
            return dumped_food_and_beverage
        
        elif  None not in (country,city) and abbreviation == None:
            food_and_beverage = Food_and_Beverage.query.join(Location, 
            Food_and_Beverage.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage,many = True)
            return dumped_food_and_beverage
        
        elif country != None and None in (city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Food_and_Beverage.query.join(Location, 
                Food_and_Beverage.location_id == Location.id).filter(Location.country == country)\
                .order_by(Food_and_Beverage.item_category.asc(),
                Food_and_Beverage.purchase_point.asc(),Food_and_Beverage.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.foodbeverageresource',
                key_name = 'results',
                schema = food_and_beverage_schema
            )
            paginated_foodbeverage = pagination_helper.paginate_query()
            return paginated_foodbeverage
        
        elif None in (country,city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Food_and_Beverage.query.join(Location, 
                Food_and_Beverage.location_id == Location.id)\
                .order_by(Food_and_Beverage.item_category.asc(),
                Food_and_Beverage.purchase_point.asc(),Food_and_Beverage.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.foodbeverageresource',
                key_name = 'results',
                schema = food_and_beverage_schema
            )
            paginated_foodbeverage = pagination_helper.paginate_query()
            return paginated_foodbeverage
        
        elif city != None and None in (country,abbreviation):
            food_and_beverage = Food_and_Beverage.query.join(Location, 
            Food_and_Beverage.location_id == Location.id).filter(Location.city == city)\
            .order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage,many = True)
            return dumped_food_and_beverage
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Food_and_Beverage.query(Food_and_Beverage.id,
                Food_and_Beverage.item_category,Food_and_Beverage.purchase_point,
                Food_and_Beverage.item,
                (Food_and_Beverage.price * Currency.usd_to_local_exchange_rate).label("price"),
                Food_and_Beverage.location_id).join(Location, Food_and_Beverage.location_id == Location.id)\
                .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
                .order_by(Food_and_Beverage.item_category.asc(),
                Food_and_Beverage.purchase_point.asc(),Food_and_Beverage.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.foodbeverageresource',
                key_name = 'results',
                schema = food_and_beverage_schema
            )
            paginated_foodbeverage = pagination_helper.paginate_query()
            return paginated_foodbeverage
    
    def post(self):
        food_and_beverage_dict = request.get_json()
        request_not_empty(food_and_beverage_dict)
        validate_request(food_and_beverage_schema,food_and_beverage_dict)
        
        try:
            location_city = food_and_beverage_dict['location']['city']
            location = Location.query.filter_by(city = location_city).first()

            if location is None:
                response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            food_and_beverage = Food_and_Beverage(item_category = food_and_beverage_dict['item_category'], 
            purchase_point = food_and_beverage_dict['purchase_point'],
            item = food_and_beverage_dict['item'],
            price = food_and_beverage_dict['price'])
            food_and_beverage.add(food_and_beverage)
            query = Food_and_Beverage.query.get(food_and_beverage.id)
            dump_result = food_and_beverage_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def patch(self,id):
        food_and_beverage = Food_and_Beverage.query.get_or_404(id)
        
        food_and_beverage_dict = request.get_json(force = True)
        request_not_empty(food_and_beverage_dict)
        validate_request(food_and_beverage_schema,food_and_beverage_dict)

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
    
    def delete(self,id):
        food_and_beverage = Food_and_Beverage.query.get_or_404(id)
        
        try:
            delete_object(food_and_beverage)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)

class ChildcareResource(Resource):
    @jwt_required
    def get(self,id=None,country=None,city=None,abbreviation=None):

        if id != None:
            childcare = Childcare.query.get_or_404(id)
            dumped_childcare = childcare_schema.dump(childcare)
            return dumped_childcare

        elif None not in (country,city,abbreviation):
            childcare = Childcare.query(Childcare.id, Childcare.type,
            (Childcare.annual_price * Currency.usd_to_local_exchange_rate).label("annual_price"),
            Childcare.location_id).join(Location, Childcare.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Childcare.type.asc()).all().get_or_404()
            dumped_childcare = childcare_schema.dump(childcare._asdict(),many = True)
            return dumped_childcare
        
        elif  None not in (country,city) and abbreviation == None:
            childcare = Childcare.query.join(Location, 
            Childcare.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Childcare.type.asc()).all().get_or_404()
            dumped_childcare = childcare_schema.dump(childcare,many = True)
            return dumped_childcare
        
        elif country != None and None in (city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Childcare.query.join(Location, 
                Childcare.location_id == Location.id).filter(Location.country == country)\
                .order_by(Childcare.type.asc(), Childcare.annual_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.childcareresource',
                key_name = 'results',
                schema = childcare_schema
            )
            paginated_childcare = pagination_helper.paginate_query()
            return paginated_childcare
        
        elif None in (country,city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Childcare.query.join(Location, 
                Childcare.location_id == Location.id)\
                .order_by(Childcare.type.asc(), Childcare.annual_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.childcareresource',
                key_name = 'results',
                schema = childcare_schema
            )
            paginated_childcare = pagination_helper.paginate_query()
            return paginated_childcare
        
        elif city != None and None in (country,abbreviation):
            childcare = Childcare.query.join(Location, 
            Childcare.location_id == Location.id).filter(Location.city == city)\
            .order_by(Childcare.type.asc()).all().get_or_404()
            dumped_childcare = utilities_schema.dump(childcare,many = True)
            return dumped_childcare
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Childcare.query(Childcare.id, Childcare.type,
                (Childcare.annual_price * Currency.usd_to_local_exchange_rate).label("annual_price"),
                Childcare.location_id).join(Location, Childcare.location_id == Location.id)\
                .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
                .order_by(Childcare.type.asc(), Childcare.annual_price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.childcareresource',
                key_name = 'results',
                schema = childcare_schema
            )
            paginated_childcare = pagination_helper.paginate_query()
            return paginated_childcare
    
    def post(self):
        childcare_dict = request.get_json()
        request_not_empty(childcare_dict)
        validate_request(childcare_schema,childcare_dict)
        
        try:
            location_city = childcare_dict['location']['city']
            location = Location.query.filter_by(city = location_city).first()

            if location is None:
                response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            childcare = Childcare(type = childcare_dict['type'], 
            annual_price = childcare_dict['annual_price'])
            childcare.add(childcare)
            query = Childcare.query.get(childcare.id)
            dump_result = childcare_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def patch(self,id):
        childcare = Childcare.query.get_or_404(id)
        
        childcare_dict = request.get_json(force = True)
        request_not_empty(childcare_dict)
        validate_request(childcare_schema,childcare_dict)

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
    
    def delete(self,id):
        childcare = Childcare.query.get_or_404(id)
        
        try:
            delete_object(childcare)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)

class ApparelResource(Resource):
    @jwt_required
    def get(self,id=None,country=None,city=None,abbreviation=None):

        if id != None:
            apparel = Apparel.query.get_or_404(id)
            dumped_apparel = apparel_schema.dump(apparel)
            return dumped_apparel

        elif None not in (country,city,abbreviation):
            apparel = Apparel.query(Apparel.id, Apparel.item,
            (Apparel.price * Currency.usd_to_local_exchange_rate).label("price"),
            Apparel.location_id).join(Location, Apparel.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Apparel.item.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel._asdict(),many = True)
            return dumped_apparel
        
        elif  None not in (country,city) and abbreviation == None:
            apparel = Apparel.query.join(Location, 
            Apparel.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Apparel.item.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel,many = True)
            return dumped_apparel
        
        elif country != None and None in (city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Apparel.query.join(Location, 
                Apparel.location_id == Location.id).filter(Location.country == country)\
                .order_by(Apparel.item.asc(),Apparel.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.apparelresource',
                key_name = 'results',
                schema = apparel_schema
            )
            paginated_apparel = pagination_helper.paginate_query()
            return paginated_apparel
        
        elif None in (country,city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Apparel.query.join(Location, 
                Apparel.location_id == Location.id)\
                .order_by(Apparel.item.asc(),Apparel.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.apparelresource',
                key_name = 'results',
                schema = apparel_schema
            )
            paginated_apparel = pagination_helper.paginate_query()
            return paginated_apparel
        
        elif city != None and None in (country,abbreviation):
            apparel = Apparel.query.join(Location, 
            Apparel.location_id == Location.id).filter(Location.city == city)\
            .order_by(Apparel.item.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel,many = True)
            return dumped_apparel
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Apparel.query(Apparel.id, Apparel.item,
                (Apparel.price * Currency.usd_to_local_exchange_rate).label("price"),
                Apparel.location_id).join(Location, Apparel.location_id == Location.id)\
                .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
                .order_by(Apparel.item.asc(),Apparel.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.apparelresource',
                key_name = 'results',
                schema = apparel_schema
            )
            paginated_apparel = pagination_helper.paginate_query()
            return paginated_apparel
    
    def post(self):
        apparel_dict = request.get_json()
        request_not_empty(apparel_dict)
        validate_request(apparel_schema,apparel_dict)
        
        try:
            location_city = apparel_dict['location']['city']
            location = Location.query.filter_by(city = location_city).first()

            if location is None:
                response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            apparel = Apparel(item = apparel_dict['item'], 
            price = apparel_dict['price'])
            apparel.add(apparel)
            query = Apparel.query.get(apparel.id)
            dump_result = apparel_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
  
    def patch(self,id):
        apparel = Apparel.query.get_or_404(id)
        
        apparel_dict = request.get_json(force = True)
        request_not_empty(apparel_dict)
        validate_request(apparel_schema,apparel_dict)

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

    def delete(self,id):
        apparel = Apparel.query.get_or_404(id)
        
        try:
            delete_object(apparel)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)

class LeisureResource(Resource):
    @jwt_required
    def get(self,id=None,country=None,city=None,abbreviation=None):

        if id != None:
            leisure = Leisure.query.get_or_404(id)
            dumped_leisure = leisure_schema.dump(leisure)
            return dumped_leisure

        elif None not in (country,city,abbreviation):
            leisure = Leisure.query(Leisure.id, Leisure.activity,
            (Leisure.price * Currency.usd_to_local_exchange_rate).label("price"),
            Leisure.location_id).join(Location, 
            Leisure.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Leisure.activity.asc()).all().get_or_404()
            dumped_leisure = leisure_schema.dump(leisure._asdict(),many = True)
            return dumped_leisure
        
        elif  None not in (country,city) and abbreviation == None:
            leisure = Leisure.query.join(Location, 
            Leisure.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Leisure.activity.asc()).all().get_or_404()
            dumped_leisure = leisure_schema.dump(leisure,many = True)
            return dumped_leisure
        
        elif country != None and None in (city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Leisure.query.join(Location, 
                Leisure.location_id == Location.id).filter(Location.country == country)\
                .order_by(Leisure.activity.asc(),Leisure.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.leisureresource',
                key_name = 'results',
                schema = leisure_schema
            )
            paginated_leisure = pagination_helper.paginate_query()
            return paginated_leisure
        
        elif None in (country,city,abbreviation):
            pagination_helper = PaginationHelper(
                request,
                query = Leisure.query.join(Location, 
                Leisure.location_id == Location.id)\
                .order_by(Leisure.activity.asc(),Leisure.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.leisureresource',
                key_name = 'results',
                schema = leisure_schema
            )
            paginated_leisure = pagination_helper.paginate_query()
            return paginated_leisure
        
        elif city != None and None in (country,abbreviation):
            leisure = Leisure.query.join(Location, 
            Leisure.location_id == Location.id).filter(Location.city == city)\
            .order_by(Leisure.activity.asc()).all().get_or_404()
            dumped_leisure = leisure_schema.dump(leisure,many = True)
            return dumped_leisure
        
        else:
            pagination_helper = PaginationHelper(
                request,
                query = Leisure.query(Leisure.id, Leisure.activity,
                (Leisure.price * Currency.usd_to_local_exchange_rate).label("price"),
                Leisure.location_id).join(Location, 
                Leisure.location_id == Location.id)\
                .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
                .order_by(Leisure.activity.asc(),Leisure.price.asc()).all().get_or_404(),
                resource_for_url = 'cost_of_living.leisureresource',
                key_name = 'results',
                schema = leisure_schema
            )
            paginated_leisure = pagination_helper.paginate_query()
            return paginated_leisure
    
    def post(self):
        leisure_dict = request.get_json()
        request_not_empty(leisure_dict)
        validate_request(leisure_schema,leisure_dict)
        
        try:
            location_city = leisure_dict['location']['city']
            location = Location.query.filter_by(city = location_city).first()

            if location is None:
                response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            leisure = Leisure(activity = leisure_dict['activity'], 
            price = leisure_dict['price'])
            leisure.add(leisure)
            query = Leisure.query.get(leisure.id)
            dump_result = leisure_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def patch(self,id):
        leisure = Leisure.query.get_or_404(id)
        
        leisure_dict = request.get_json(force = True)
        request_not_empty(leisure_dict)
        validate_request(leisure_schema,leisure_dict)

        try:
            if 'item' in leisure_dict and leisure_dict['item'] != None:
                leisure.item = leisure_dict['item']
            if 'price' in leisure_dict and \
            leisure_dict['price'] != None:
                leisure.price = leisure_dict['price']
        
            leisure.update()
            self.get(id)

        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
    
    def delete(self,id):
        leisure = Leisure.query.get_or_404(id)
        
        try:
            delete_object(leisure)
        
        except SQLAlchemyError as e:
            sql_alchemy_error_response(e)
        

cost_of_living.add_resource(UserResource,'/auth/user')
cost_of_living.add_resource(LoginResource,'/auth/login')
cost_of_living.add_resource(LogoutResource, '/auth/logout')
cost_of_living.add_resource(ResetPasswordResource,'/user/password_reset')        
cost_of_living.add_resource(CurrencyResource, '/currencies/','/currencies/<int:id>')
cost_of_living.add_resource(LocationListResource, '/locations/','/locations/<int:id>')
cost_of_living.add_resource(HomePurchaseResource, '/homepurchase/', '/homepurchase/<int:id>','/homepurchase/<string:country>/<string:city>/\
<string:abbreviation>','/homepurchase/<string:country>/<string:city>', '/homepurchase/<string:country>', 
'/homepurchase/<string:city>/<string:abbreviation>', '/homepurchase/<string:city>/<string:abbreviation>')
cost_of_living.add_resource(RentResource, '/rent/', '/rent/<int:id>','/rent/<string:country>/<string:city>/\
<string:abbreviation>','/rent/<string:country>/<string:city>', '/rent/<string:country>', 
'/rent/<string:city>/<string:abbreviation>', '/rent/<string:city>/<string:abbreviation>')
cost_of_living.add_resource(UtilitiesResource,'/utilities/', '/utilities/<int:id>','/utilities/<string:country>/<string:city>/\
<string:abbreviation>','/utilities/<string:country>/<string:city>', '/utiilties/<string:country>', 
'/utilities/<string:city>/<string:abbreviation>', '/utilities/<string:city>/<string:abbreviation>')
cost_of_living.add_resource(TransportationResource, '/transportation/', '/transportation/<int:id>','/transportation/<string:country>/<string:city>/\
<string:abbreviation>','/transportation/<string:country>/<string:city>', '/transportation/<string:country>', 
'/transportation/<string:city>/<string:abbreviation>', '/transportation/<string:city>/<string:abbreviation>')
cost_of_living.add_resource(FoodBeverageResource,'/foodbeverage/', '/foodbeverage/<int:id>','/foodbeverage/<string:country>/<string:city>/\
<string:abbreviation>','/foodbeverage/<string:country>/<string:city>', '/foodbeverage/<string:country>', 
'/foodbeverage/<string:city>/<string:abbreviation>', '/foodbeverage/<string:city>/<string:abbreviation>')
cost_of_living.add_resource(ChildcareResource,'/childcare/', '/childcare/<int:id>','/childcare/<string:country>/<string:city>/\
<string:abbreviation>','/childcare/<string:country>/<string:city>', '/childcare/<string:country>', 
'/childcare/<string:city>/<string:abbreviation>', '/childcare/<string:city>/<string:abbreviation>')
cost_of_living.add_resource(ApparelResource, '/apparel/', '/apparel/<int:id>','/apparel/<string:country>/<string:city>/\
<string:abbreviation>','/apparel/<string:country>/<string:city>', '/apparel/<string:country>', 
'/apparel/<string:city>/<string:abbreviation>', '/apparel/<string:city>/<string:abbreviation>')
cost_of_living.add_resource(LeisureResource, '/leisure/', '/leisure/<int:id>','/leisure/<string:country>/<string:city>/\
<string:abbreviation>','/leisure/<string:country>/<string:city>', '/leisure/<string:country>', 
'/leisure/<string:city>/<string:abbreviation>', '/leisure/<string:city>/<string:abbreviation>')
