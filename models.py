import jwt
import datetime
import re
from marshmallow import Schema, fields, INCLUDE
from marshmallow import validate
from passlib.apps import custom_app_context as password_context
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

orm = SQLAlchemy()
ma = Marshmallow()

class ResourceAddUpdateDelete():
    def add(self,resource):
        orm.session.add(resource)
        return orm.session.commit()
    
    def update(self):
        return orm.session.commit()
    
    def delete(self,resource):
        orm.session.delete(resource)
        return orm.session.commit()

class User(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    email = orm.Column(orm.String(50),unique = True,nullable = False)
    password_hash = orm.Column(orm.String(120),nullable = False)
    admin = orm.Column(orm.Boolean, default = False)
    creation_date = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def check_password_strength_and_hash_if_ok(self, password):
        if len(password) < 8:
            return 'The password is too short. Please, specify a password with at least 8 characters'
        if len(password) > 32:
            return 'The password is too long. Please, specify a password with no more than 32 characters'
        if re.search(r'[A-Z]', password) == None:
            return 'The password must include at least one uppercase letter'
        if re.search(r'[a-z]', password) == None:
            return 'The password must include at least one lowercase letter'
        if re.search(r'\d', password) == None:
            return 'The password must include at least one digit'
        if re.search(r"[ !#$%&'()*+,-./[\\\]^_`{|}~"+r'"]', password) == None:
            return 'The password must include at least one symbol'
        self.password_hash = password_context.hash(password)
    
    def verify_password(self,password):
        return password_context.verify(password, self.password_hash)

    def __init__(self,email,admin=None):
        self.email = email
        if admin == 'Code only I know': # Delete this piece of code once I create myself as admin
            self.admin = True

    def encode_auth_token(self,user_id):
        # Generate Auth Token
        try:
            payload = {
                'exp':datetime.datetime.utcnow() + datetime.timedelta(days = 0,seconds = 5),
                'iat':datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode (
                payload,
                "secret_key",
                algorithm = 'HS256'
            )
        except Exception as e:
            return e
    
    @staticmethod
    def decode_auth_token(auth_token):
        # Decode Auth Token
        try:
            payload = jwt.decode(auth_token, "secret_key")
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again'
        
class BlacklistToken(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    token = orm.Column(orm.String(500),unique = True,nullable = False)
    blacklisted_on = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,token):
        self.token = token

    @staticmethod
    def check_blacklist(auth_token):
        # Check if auth token has been blacklisted
        blacklisted_token=BlacklistToken.query.filter_by(token = str(auth_token)).first()
        if blacklisted_token:
            return True
        else:
            return False

class Currency(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    abbreviation = orm.Column(orm.String(3),unique = True,nullable = False)
    usd_to_local_exchange_rate = orm.Column(orm.Float,nullable = False) # USD is the default currency
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)
    location = orm.relationship('Location',backref = orm.backref('currency_abbreviation'))

    @classmethod
    def is_abbreviation_unique(cls, id, abbreviation):
        existing_abbreviation = cls.query.filter_by(abbreviation=abbreviation).first()
        if existing_abbreviation is None:
            return True
        else:
            if existing_abbreviation.id == id:
                return True
            else:
                return False

    def __init__(self,abbreviation,usd_to_local_exchange_rate):
        self.abbreviation = abbreviation
        self.usd_to_local_exchange_rate = usd_to_local_exchange_rate

class Location(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    country = orm.Column(orm.String(50),nullable = False)
    city = orm.Column(orm.String(50),unique = True,nullable = False)
    currency_id = orm.Column(orm.Integer,orm.ForeignKey('currency.id'),nullable = False)
    home_purchase = orm.relationship('Home_Purchase',backref = orm.backref('location'))
    rent = orm.relationship('Rent',backref = orm.backref('location'))
    utlities = orm.relationship('Utilities',backref = orm.backref('location'))
    transportation = orm.relationship('Transportation',backref = orm.backref('location'))
    food_and_beverage = orm.relationship('Food_and_Beverage',backref = orm.backref('location'))
    childcare = orm.relationship('Childcare',backref = orm.backref('location'))
    apparel = orm.relationship('Apparel',backref = orm.backref('location'))
    leisure = orm.relationship('Leisure',backref = orm.backref('location'))

    def __init__(self,country,city,currency_abbreviation):
        self.country = country
        self.city = city
        self.currency_abbreviation = currency_abbreviation
    
class Home_Purchase(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    property_location = orm.Column(orm.String(30),nullable = False)
    price_per_sqm = orm.Column(orm.Float,nullable = False)
    mortgage_interest = orm.Column(orm.Float,nullable = False)
    location_id = orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique = True,nullable = False)
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,property_location,price_per_sqm,mortgage_interest):
        self.property_location = property_location
        self.price_per_sqm = price_per_sqm
        self.mortgage_interest = mortgage_interest

class Rent(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    property_location = orm.Column(orm.String(30),nullable = False)
    bedrooms = orm.Column(orm.Integer,nullable = False)
    monthly_price = orm.Column(orm.Float,nullable = False)
    location_id = orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique = True,nullable = False)
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,property_location,bedrooms,monthly_price):
        self.property_location = property_location
        self.bedrooms = bedrooms
        self.monthly_price = monthly_price

class Utilities(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    utility = orm.Column(orm.String(80),nullable = False)
    monthly_price = orm.Column(orm.Float,nullable = False)
    location_id = orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique = True,nullable = False)
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,utility,monthly_price):
        self.utility = utility
        self.monthly_price = monthly_price

class Transportation(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    type = orm.Column(orm.String(70),nullable = False)
    price = orm.Column(orm.Float,nullable = False)
    location_id = orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique = True,nullable = False)
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,type,price):
        self.type = type
        self.price = price

class Food_and_Beverage(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    item_category = orm.Column(orm.String(20),nullable = False)
    purchase_point = orm.Column(orm.String(20),nullable = False)
    item = orm.Column(orm.String(30),nullable = False)
    price = orm.Column(orm.Float,nullable = False)
    location_id = orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique = True,nullable = False)
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,item_category,purchase_point,item,price):
        self.item_category = item_category
        self.purchase_point = purchase_point
        self.item = item
        self.price = price

class Childcare(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    type = orm.Column(orm.String(80),nullable = False)
    annual_price = orm.Column(orm.Float,nullable = False)
    location_id = orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique = True,nullable = False)
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,type,annual_price):
        self.type = type
        self.annual_price = annual_price

class Apparel(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    item = orm.Column(orm.String(70),nullable = False)
    price = orm.Column(orm.Float,nullable = False)
    location_id = orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique = True,nullable = False)
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,item,price):
        self.item = item
        self.price = price

class Leisure(orm.Model,ResourceAddUpdateDelete):
    id = orm.Column(orm.Integer,primary_key = True)
    activity = orm.Column(orm.String(50),nullable = False)
    price = orm.Column(orm.Float,nullable = False)
    location_id = orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique = True,nullable = False)
    last_updated = orm.Column(orm.TIMESTAMP,server_default = orm.func.current_timestamp(),nullable = False)

    def __init__(self,activity,price):
        self.activity = activity
        self.price = price

class UserSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    email = fields.String()
    password = fields.String()

class CurrencySchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    abbreviation = fields.String(validate = validate.Length(3))
    usd_to_local_exchange_rate = fields.Float()
    last_updated = fields.DateTime()
    location = fields.Nested('LocationSchema',only = ['country'],many = True)

class LocationSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    country = fields.String(required = True)
    city = fields.String(required = True)
    currency = fields.Nested(CurrencySchema,only = ['id','abbreviation'])

class Home_PurchaseSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    location = fields.Nested(LocationSchema,only = ['id','country','city'])
    property_location = fields.String(validate = validate.Length(10))
    price_per_sqm = fields.Float()
    mortgage_interest = fields.Float()
    last_updated = fields.DateTime()

class RentSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    location = fields.Nested(LocationSchema,only = ['id','country','city'])
    property_location = fields.String(validate = validate.Length(10))
    bedrooms = fields.Float()
    monthly_price = fields.Float()
    last_updated = fields.DateTime()

class UtilitiesSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    location = fields.Nested(LocationSchema,only = ['id','country','city'])
    utility = fields.String()
    monthly_price = fields.Float()
    last_updated = fields.DateTime()

class TransportationSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    location = fields.Nested(LocationSchema,only = ['id','country','city'])
    type = fields.String()
    price = fields.Float()
    last_updated = fields.DateTime()

class Food_and_BeverageSchema(ma.Schema):
    id = fields.Integer(dumpy_only = True)
    location = fields.Nested(LocationSchema,only = ['id','country','city'])
    item_category = fields.String()
    purchase_point = fields.String()
    item = fields.String()
    price = fields.Float()
    last_updated = fields.DateTime()

class ChildcareSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    location = fields.Nested(LocationSchema,only = ['id','country','city'])
    type = fields.String()
    annual_price = fields.Float()
    last_updated = fields.DateTime()

class ApparelSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    location = fields.Nested(LocationSchema,only = ['id','country','city'])
    item = fields.String()
    price = fields.Float()
    last_updated = fields.DateTime()

class LeisureSchema(ma.Schema):
    id = fields.Integer(dump_only = True)
    location = fields.Nested(LocationSchema,only = ['id','country','city'])
    activity = fields.String()
    price = fields.Float()
    last_updated = fields.DateTime()








