from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required
from httpstatus import HttpStatus
from models import *
from sqlalchemy.exc import SQLAlchemyError

cost_of_living_blueprint = Blueprint('cost_of_living', __name__)
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
            return response, HttpStatus.unauthorized_401.value
                
    def post(self):
        user_register_dict = request.get_json()
        if not user_register_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value

        user = User.query.filter_by(email = user_register_dict['email']).first()
        if not user:
            try:
                user = User(email = user_register_dict['email'], 
                password_hash = user_register_dict['password_hash'])
                user.add(user)
                auth_token = user.encode_auth_token(user.id)
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
        if not user_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value

        try:
            user = User.query.filter_by(email = user_dict['email']).first()
            if user.verify_password(user_dict['password']):
                auth_token = user.encode_auth_token(user.id)
                if auth_token:
                    response = {
                    'message': 'Successfully logged in.',
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
    def post(self):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(" ")[1]
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

        if not reset_password_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        try:
            user = User.query.filter_by(email = reset_password_dict['email']).first()
            if user:
                user.modify_password(new_password = reset_password_dict['password'])
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
            currencies = Currency.query.all()
            dumped_currencies = currency_schema.dump(currencies,many = True)
            return dumped_currencies
    
    def post(self):
        currency_dict = request.get_json()

        if not currency_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value

        errors = currency_schema.validate(currency_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

        try:
            currency = Currency(abbreviation = currency_dict['abbreviation'],
            usd_to_local_exchange_rate = currency_dict['usd_to_local_exchange_rate'])
            currency.add(currency)
            query = Currency.query.get(currency.id)
            dump_result = currency_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def patch(self,id):
        currency = Currency.query.get_or_404(id)
        
        currency_dict = request.get_json(force = True)
        if not currency_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = currency_schema.validate(currency_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

        try:
            if 'abbreviation' in currency_dict and currency_dict['abbreviation'] != None:
                currency.abbreviation = currency_dict['abbreviation']
            if 'usd_to_local_exchange_rate' in currency_dict and \
            currency_dict['usd_to_local_exchange_rate'] != None:
                currency.usd_to_local_exchange_rate = currency_dict['usd_to_local_exchange_rate']
        
            currency.update()
            self.get(id)

        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def delete(self,id):
        currency = Currency.query.get_or_404(id)
        
        try:
            currency.delete(currency)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value

class LocationListResource(Resource):
    @jwt_required
    def get(self,id):

        if id != None:
            location = Location.query.get_or_404(id)
            dumped_location = location_schema.dump(location)
            return dumped_location

        else:
            locations = Location.query.all()
            dumped_locations = location_schema.dump(locations,many = True)
            return dumped_locations
    
    def post(self):
        location_dict = request.get_json()
        if not location_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = location_schema.validate(location_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
        try:
            currency_abbreviation = location_dict['currency']['abbreviation']
            currency = Currency.query.filter_by(abbreviation = currency_abbreviation).first()

            if currency is None:
                response = {'message': 'Specified currency doesnt exist in /currencies/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            location = Location(country = location_dict['country'], city = location_dict['city'])
            location.add(location)
            query = Location.query.get(location.id)
            dump_result = location_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def delete(self,id):
        location = Location.query.get_or_404(id)
        
        try:
            location.delete(location)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value

class Home_Purchase_Resource(Resource):
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
            dumped_home_purchase = home_purchase_schema.dump(home_purchase._asdict(),many=True)
            return dumped_home_purchase
        
        elif  None not in (country,city) and abbreviation == None:
            home_purchase = Home_Purchase.query.join(Location, 
            Home_Purchase.location_id == Location.id).filter(Location.country == country,
            Location.city == city).order_by(Home_Purchase.property_location.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase,many=True)
            return dumped_home_purchase
        
        elif country != None and None in (city,abbreviation):
            home_purchase = Home_Purchase.query.join(Location, 
            Home_Purchase.location_id == Location.id).filter(Location.country == country)\
            .order_by(Home_Purchase.property_location.asc(), Home_Purchase.price_per_sqm.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase,many = True)
            return dumped_home_purchase
        
        elif None in (country,city,abbreviation):
            home_purchase = Home_Purchase.query.join(Location, 
            Home_Purchase.location_id == Location.id)\
            .order_by(Home_Purchase.property_location.asc(), Home_Purchase.price_per_sqm.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase,many = True)
            return dumped_home_purchase
        
        elif city != None and None in (country,abbreviation):
            home_purchase = Home_Purchase.query.join(Location, 
            Home_Purchase.location_id == Location.id).filter(Location.city == city)\
            .order_by(Home_Purchase.property_location.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase,many = True)
            return dumped_home_purchase
        
        else:
            home_purchase = Home_Purchase.query(Home_Purchase.id,
            Home_Purchase.property_location, 
            (Home_Purchase.price_per_sqm * Currency.usd_to_local_exchange_rate).label("price_per_sqm"),
            Home_Purchase.mortgage_interest,
            Home_Purchase.location_id).join(Location, Home_Purchase.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Home_Purchase.property_location.asc(),Home_Purchase.price_per_sqm.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase._asdict(),many = True)
            return dumped_home_purchase
 
    def post(self):
        home_purchase_dict = request.get_json()
        if not home_purchase_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = home_purchase_schema.validate(home_purchase_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
        try:
            location_city = home_purchase_dict['location']['city']
            location = Location.query.filter_by(city = location_city).first()

            if location is None:
                response = {'message': 'Specified city doesnt exist in /locations/ API endpoint'}
                return response, HttpStatus.notfound_404.value
            
            home_purchase = Home_Purchase(property_location = home_purchase_dict['property_location'], 
            price_per_sqm = home_purchase_dict['price_per_sqm'], 
            mortgage_interest = home_purchase_dict['mortgage_interest'])
            home_purchase.add(home_purchase)
            query = Home_Purchase.query.get(home_purchase.id)
            dump_result = home_purchase_schema.dump(query)
            return dump_result, HttpStatus.created_201.value

        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def patch(self,id):
        home_purchase = Home_Purchase.query.get_or_404(id)
        
        home_purchase_dict = request.get_json(force = True)
        if not home_purchase_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = home_purchase_schema.validate(home_purchase_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value

    def delete(self,id):
        home_purchase = Home_Purchase.query.get_or_404(id)
        
        try:
            home_purchase.delete(home_purchase)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value

class Rent_Resource(Resource):
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
            rent = Rent.query.join(Location, 
            Rent.location_id == Location.id).filter(Location.country == country)\
            .order_by(Rent.bedrooms.asc(), Rent.monthly_price.asc()).all().get_or_404()
            dumped_rent = rent_schema.dump(rent,many = True)
            return dumped_rent
        
        elif None in (country,city,abbreviation):
            rent = Rent.query.join(Location, 
            Rent.location_id == Location.id)\
            .order_by(Rent.bedrooms.asc(), Rent.monthly_price.asc()).all().get_or_404()
            dumped_rent = rent_schema.dump(rent,many = True)
            return dumped_rent
        
        elif city != None and None in (country,abbreviation):
            rent = Rent.query.join(Location, 
            Rent.location_id == Location.id).filter(Location.city == city)\
            .order_by(Rent.bedrooms.asc()).all().get_or_404()
            dumped_rent = rent_schema.dump(rent,many = True)
            return dumped_rent
        
        else:
            rent = Rent.query(Rent.id, Rent.property_location,Rent.bedrooms,
            (Rent.monthly_price * Currency.usd_to_local_exchange_rate).label("monthly_price"),
            Rent.location_id).join(Location, Rent.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Rent.bedrooms.asc(),Rent.monthly_price.asc()).all().get_or_404()
            dumped_rent = rent_schema.dump(rent._asdict(),many = True)
            return dumped_rent

    def post(self):
        rent_dict = request.get_json()
        if not rent_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = rent_schema.validate(rent_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def patch(self,id):
        rent = Rent.query.get_or_404(id)
        
        rent_dict = request.get_json(force = True)
        if not rent_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = rent_schema.validate(rent_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def delete(self,id):
        rent = Rent.query.get_or_404(id)
        
        try:
            rent.delete(rent)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value

class Utilities_Resource(Resource):
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
            utilities = Utilities.query.join(Location, 
            Utilities.location_id == Location.id).filter(Location.country == country)\
            .order_by(Utilities.utility.asc(), Utilities.monthly_price.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities,many = True)
            return dumped_utilities
        
        elif None in (country,city,abbreviation):
            utilities = Utilities.query.join(Location, 
            Utilities.location_id == Location.id)\
            .order_by(Utilities.utility.asc(), Utilities.monthly_price.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities,many = True)
            return dumped_utilities
        
        elif city != None and None in (country,abbreviation):
            utilities = Utilities.query.join(Location, 
            Utilities.location_id == Location.id).filter(Location.city == city)\
            .order_by(Utilities.utility.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities,many = True)
            return dumped_utilities
        
        else:
            utilities = Utilities.query(Utilities.id,Utilities.utility,
            (Utilities.monthly_price * Currency.usd_to_local_exchange_rate).label("monthly_price"),
            Utilities.location_id).join(Location, 
            Utilities.location_id == Location.id).join(Location, 
            Utilities.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Utilities.utility.asc(),Utilities.monthly_price.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities._asdict(),many = True)
            return dumped_utilities
    
    def post(self):
        utilities_dict = request.get_json()
        if not utilities_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = utilities_schema.validate(utilities_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def patch(self,id):
        utilities = Utilities.query.get_or_404(id)
        
        utilities_dict = request.get_json(force = True)
        if not utilities_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = utilities_schema.validate(utilities_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

        try:
            if 'utility' in utilities_dict and utilities_dict['utility'] != None:
                utilities.utility = utilities_dict['utility']
            if 'monthly_price' in utilities_dict and \
            utilities_dict['monthly_price'] != None:
                utilities.monthly_price = utilities_dict['monthly_price']
        
            utilities.update()
            self.get(id)

        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def delete(self,id):
        utilities = Utilities.query.get_or_404(id)
        
        try:
            utilities.delete(utilities)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value


class Transportation_Resource(Resource):
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
            transportation = Transportation.query.join(Location, 
            Transportation.location_id == Location.id).filter(Location.country == country)\
            .order_by(Transportation.type.asc(), Transportation.price.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation,many = True)
            return dumped_transportation
        
        elif None in (country,city,abbreviation):
            transportation = Transportation.query.join(Location, 
            Transportation.location_id == Location.id)\
            .order_by(Transportation.type.asc(), Transportation.price.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation,many = True)
            return dumped_transportation
        
        elif city != None and None in (country,abbreviation):
            transportation = Transportation.query.join(Location, 
            Transportation.location_id == Location.id).filter(Location.city == city)\
            .order_by(Transportation.type.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation,many = True)
            return dumped_transportation
        
        else:
            transportation = Transportation.query(Transportation.id,Transportation.type,
            (Transportation.price * Currency.usd_to_local_exchange_rate).label("price"),
            Transportation.location_id).join(Location, Transportation.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Transportation.type.asc(),Transportation.price.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation._asdict(),many = True)
            return dumped_transportation
    
    def post(self):
        transportation_dict = request.get_json()
        if not transportation_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = transportation_schema.validate(transportation_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def patch(self,id):
        transportation = Transportation.query.get_or_404(id)
        
        transportation_dict = request.get_json(force = True)
        if not transportation_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = transportation_schema.validate(transportation_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

        try:
            if 'type' in transportation_dict and transportation_dict['type'] != None:
                transportation.type = transportation_dict['type']
            if 'price' in transportation_dict and \
            transportation_dict['price'] != None:
                transportation.price = transportation_dict['price']
        
            transportation.update()
            self.get(id)

        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def delete(self,id):
        transportation = Transportation.query.get_or_404(id)
        
        try:
            transportation.delete(transportation)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value

class Food_and_Beverage_Resource(Resource):
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
            food_and_beverage = Food_and_Beverage.query.join(Location, 
            Food_and_Beverage.location_id == Location.id).filter(Location.country == country)\
            .order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc(),Food_and_Beverage.price.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage,many = True)
            return dumped_food_and_beverage
        
        elif None in (country,city,abbreviation):
            food_and_beverage = Food_and_Beverage.query.join(Location, 
            Food_and_Beverage.location_id == Location.id)\
            .order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc(),Food_and_Beverage.price.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage,many = True)
            return dumped_food_and_beverage
        
        elif city != None and None in (country,abbreviation):
            food_and_beverage = Food_and_Beverage.query.join(Location, 
            Food_and_Beverage.location_id == Location.id).filter(Location.city == city)\
            .order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage,many = True)
            return dumped_food_and_beverage
        
        else:
            food_and_beverage = Food_and_Beverage.query(Food_and_Beverage.id,
            Food_and_Beverage.item_category,Food_and_Beverage.purchase_point,
            Food_and_Beverage.item,
            (Food_and_Beverage.price * Currency.usd_to_local_exchange_rate).label("price"),
            Food_and_Beverage.location_id).join(Location, Food_and_Beverage.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc(),Food_and_Beverage.price.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage._asdict(),many = True)
            return dumped_food_and_beverage
    
    def post(self):
        food_and_beverage_dict = request.get_json()
        if not food_and_beverage_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = food_and_beverage_schema.validate(food_and_beverage_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def patch(self,id):
        food_and_beverage = Food_and_Beverage.query.get_or_404(id)
        
        food_and_beverage_dict = request.get_json(force = True)
        if not food_and_beverage_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = food_and_beverage_schema.validate(food_and_beverage_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def delete(self,id):
        food_and_beverage = Food_and_Beverage.query.get_or_404(id)
        
        try:
            food_and_beverage.delete(food_and_beverage)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value

class Childcare_Resource(Resource):
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
            childcare = Childcare.query.join(Location, 
            Childcare.location_id == Location.id).filter(Location.country == country)\
            .order_by(Childcare.type.asc(), Childcare.annual_price.asc()).all().get_or_404()
            dumped_childcare = childcare_schema.dump(childcare,many = True)
            return dumped_childcare
        
        elif None in (country,city,abbreviation):
            childcare = Childcare.query.join(Location, 
            Childcare.location_id == Location.id)\
            .order_by(Childcare.type.asc(), Childcare.annual_price.asc()).all().get_or_404()
            dumped_childcare = childcare_schema.dump(childcare,many = True)
            return dumped_childcare
        
        elif city != None and None in (country,abbreviation):
            childcare = Childcare.query.join(Location, 
            Childcare.location_id == Location.id).filter(Location.city == city)\
            .order_by(Childcare.type.asc()).all().get_or_404()
            dumped_childcare = utilities_schema.dump(childcare,many = True)
            return dumped_childcare
        
        else:
            childcare = Childcare.query(Childcare.id, Childcare.type,
            (Childcare.annual_price * Currency.usd_to_local_exchange_rate).label("annual_price"),
            Childcare.location_id).join(Location, Childcare.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Childcare.type.asc(), Childcare.annual_price.asc()).all().get_or_404()
            dumped_childcare = childcare_schema.dump(childcare._asdict(),many = True)
            return dumped_childcare
    
    def post(self):
        childcare_dict = request.get_json()
        if not childcare_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = childcare_schema.validate(childcare_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def patch(self,id):
        childcare = Childcare.query.get_or_404(id)
        
        childcare_dict = request.get_json(force = True)
        if not childcare_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = childcare_schema.validate(childcare_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

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
            childcare.delete(childcare)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value

class Apparel_Resource(Resource):
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
            apparel = Apparel.query.join(Location, 
            Apparel.location_id == Location.id).filter(Location.country == country)\
            .order_by(Apparel.item.asc(),Apparel.price.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel,many = True)
            return dumped_apparel
        
        elif None in (country,city,abbreviation):
            apparel = Apparel.query.join(Location, 
            Apparel.location_id == Location.id)\
            .order_by(Apparel.item.asc(),Apparel.price.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel,many = True)
            return dumped_apparel
        
        elif city != None and None in (country,abbreviation):
            apparel = Apparel.query.join(Location, 
            Apparel.location_id == Location.id).filter(Location.city == city)\
            .order_by(Apparel.item.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel,many = True)
            return dumped_apparel
        
        else:
            apparel = Apparel.query(Apparel.id, Apparel.item,
            (Apparel.price * Currency.usd_to_local_exchange_rate).label("price"),
            Apparel.location_id).join(Location, Apparel.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Apparel.item.asc(),Apparel.price.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel._asdict(),many = True)
            return dumped_apparel
    
    def post(self):
        apparel_dict = request.get_json()
        if not apparel_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = apparel_schema.validate(apparel_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
  
    def patch(self,id):
        apparel = Apparel.query.get_or_404(id)
        
        apparel_dict = request.get_json(force = True)
        if not apparel_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = apparel_schema.validate(apparel_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

        try:
            if 'item' in apparel_dict and apparel_dict['item'] != None:
                apparel.item = apparel_dict['item']
            if 'price' in apparel_dict and \
            apparel_dict['price'] != None:
                apparel.price = apparel_dict['price']
        
            apparel.update()
            self.get(id)

        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value

    def delete(self,id):
        apparel = Apparel.query.get_or_404(id)
        
        try:
            apparel.delete(apparel)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value

class Leisure_Resource(Resource):
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
            leisure = Leisure.query.join(Location, 
            Leisure.location_id == Location.id).filter(Location.country == country)\
            .order_by(Leisure.activity.asc(),Leisure.price.asc()).all().get_or_404()
            dumped_leisure = leisure_schema.dump(leisure,many = True)
            return dumped_leisure
        
        elif None in (country,city,abbreviation):
            leisure = Leisure.query.join(Location, 
            Leisure.location_id == Location.id)\
            .order_by(Leisure.activity.asc(),Leisure.price.asc()).all().get_or_404()
            leisure = leisure_schema.dump(leisure,many = True)
            return dumped_leisure
        
        elif city != None and None in (country,abbreviation):
            leisure = Leisure.query.join(Location, 
            Leisure.location_id == Location.id).filter(Location.city == city)\
            .order_by(Leisure.activity.asc()).all().get_or_404()
            dumped_leisure = leisure_schema.dump(leisure,many = True)
            return dumped_leisure
        
        else:
            leisure = Leisure.query(Leisure.id, Leisure.activity,
            (Leisure.price * Currency.usd_to_local_exchange_rate).label("price"),
            Leisure.location_id).join(Location, 
            Leisure.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Leisure.activity.asc(),Leisure.price.asc()).all().get_or_404()
            dumped_leisure = leisure_schema.dump(leisure._asdict(),many = True)
            return dumped_leisure
    
    def post(self):
        leisure_dict = request.get_json()
        if not leisure_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = leisure_schema.validate(leisure_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value
        
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
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def patch(self,id):
        leisure = Leisure.query.get_or_404(id)
        
        leisure_dict = request.get_json(force = True)
        if not leisure_dict:
            response = {'message': 'No input data provided'}
            return response, HttpStatus.bad_request_400.value
        
        errors = leisure_schema.validate(leisure_dict)
        if errors:
            return errors, HttpStatus.bad_request_400.value

        try:
            if 'item' in leisure_dict and leisure_dict['item'] != None:
                leisure.item = leisure_dict['item']
            if 'price' in leisure_dict and \
            leisure_dict['price'] != None:
                leisure.price = leisure_dict['price']
        
            leisure.update()
            self.get(id)

        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error": str(e)}
            return response, HttpStatus.bad_request_400.value
    
    def delete(self,id):
        leisure = Leisure.query.get_or_404(id)
        
        try:
            leisure.delete(leisure)
            response = make_response()
            return response, HttpStatus.no_content_204.value
        
        except SQLAlchemyError as e:
            orm.session.rollback()
            response = {"error":str(e)}
            return response, HttpStatus.unauthorized_401.value
        

cost_of_living.add_resource(UserResource,'/auth/user')
cost_of_living.add_resource(LoginResource,'/auth/login')
cost_of_living.add_resource(LogoutResource, '/auth/logout')
cost_of_living.add_resource(ResetPasswordResource,'/user/password_reset')        
cost_of_living.add_resource(CurrencyResource, '/currencies/','/currencies/<int:id>')
cost_of_living.add_resource(LocationListResource, '/locations/','/locations/<int:id>')
cost_of_living.add_resource(Home_Purchase_Resource,'/homepurchase/<string:country>/<string:city>/\
<string:abbreviation>', '/homepurchase/<int:id>')
cost_of_living.add_resource(Rent_Resource,'/rent/<string:country>/<string:city>/\
<string:abbreviation>','/rent/<int:id>')
cost_of_living.add_resource(Utilities_Resource,'/utilites/<string:country>/<string:city>/\
<string:abbreviation>','/utilities/<int:id>')
cost_of_living.add_resource(Transportation_Resource,'/transportation/<string:country>/<string:city>/\
<string:abbreviation>','/transportation/<int:id>')
cost_of_living.add_resource(Food_and_Beverage_Resource,'/foodbeverage/<string:country>/<string:city>/\
<string:abbreviation>','/foodbeverage/<int:id>')
cost_of_living.add_resource(Childcare_Resource,'/childcare/<string:country>/<string:city>/\
<string:abbreviation>','/childcare/<int:id>')
cost_of_living.add_resource(Apparel_Resource,'/apparel/<string:country>/<string:city>/\
<string:abbreviation>','/apparel/<int:id>')
cost_of_living.add_resource(Leisure_Resource,'/leisure/<string:country>/<string:city>/\
<string:abbreviation>','/leisure/<int:id>')
