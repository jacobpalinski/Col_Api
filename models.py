import jwt
import datetime
from marshmallow import Schema, fields
from marshmallow import validate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from passlib.apps import custom_app_context as password_context

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
    id=orm.Column(orm.Integer,primary_key=True)
    email=orm.Column(orm.String(50),unique=True,nullable=False)
    password_hash=orm.Column(orm.String(120),nullable=False)
    admin = orm.Column(orm.Boolean, default = False)
    creation_date=orm.Column(orm.TIMESTAMP,server_default=orm.func.current_timestamp(),nullable=False)

    def __init__(self,email,password,admin):
        self.email=email
        self.password_hash=password_context.hash(password)
        if admin == 'Code only I know':
            self.admin = True
    
    def verify_password(self,password):
        return password_context.verify(password, self.password_hash)
    
    def modify_password(self,new_password):
        self.password_hash = password_context.hash(new_password)

    def encode_auth_token(self,user_id):
        # Generate Auth Token
        try:
            payload={
                'exp':datetime.datetime.utcnow() + datetime.timedelta(days=1,seconds=0),
                'iat':datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                # app.config.get('SECRET_KEY')
                algorithm='HS256'
            )
        except Exception as e:
            return e
    
    @staticmethod
    def decode_auth_token(auth_token):
        # Decode Auth Token
        try:
            payload=jwt.decode(auth_token) # , app.config.get('SECRET_KEY')
            is_blacklisted_token=BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'
        
class BlacklistToken(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    token=orm.Column(orm.String(500),unique=True,nullable=False)
    blacklisted_on=orm.Column(orm.TIMESTAMP,server_default=orm.func.current_timestamp(),nullable=False)

    def __init__(self,token):
        self.token=token

    @staticmethod
    def check_blacklist(auth_token):
        # Check if auth token has been blacklisted
        blacklisted_token=BlacklistToken.query.filter_by(token=str(auth_token)).first()
        if blacklisted_token:
            return True
        else:
            return False

class Currency(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    abbreviation=orm.Column(orm.String(3),unique=True,nullable=False)
    usd_to_local_exchange_rate=orm.Column(orm.Float,nullable=False) # USD is the default currency
    location=orm.relationship('Location',backref=orm.backref('currency_abbreviation',lazy='dynamic'))

    def __init__(self,abbreviation,usd_to_local_exchange_rate):
        self.abbreviation=abbreviation
        self.usd_to_local_exchange_rate=usd_to_local_exchange_rate

class Location(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    country=orm.Column(orm.String(50),nullable=False)
    city=orm.Column(orm.String(50),unique=True,nullable=False)
    currency_id=orm.Column(orm.Integer,orm.ForeignKey('currency.id'),nullable=False)
    home_purchase=orm.relationship('Home_Purchase',backref=orm.backref('location',lazy='dynamic'))
    rent=orm.relationship('Rent',backref=orm.backref('location',lazy='dynamic'))
    utlities=orm.relationship('Utilities',backref=orm.backref('location',lazy='dynamic'))
    transportation=orm.relationship('Transportation',backref=orm.backref('location',lazy='dynamic'))
    food_and_beverage=orm.relationship('Food_and_Beverage',backref=orm.backref('location',lazy='dynamic'))
    childcare=orm.relationship('Childcare',backref=orm.backref('location',lazy='dynamic'))
    apparel=orm.relationship('Apparel',backref=orm.backref('location',lazy='dynamic'))
    leisure=orm.relationship('Leisure',backref=orm.backref('location',lazy='dynamic'))

    def __init__(self,country,city):
        self.country=country
        self.city=city
    
class Home_Purchase(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    property_location=orm.Column(orm.String(30),nullable=False)
    price_per_sqm=orm.Column(orm.Float,nullable=False)
    mortgage_interest=orm.Column(orm.Float,nullable=False)
    location_id=orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique=True,nullable=False)

    def __init__(self,property_location,price_per_sqm,mortgage_interest):
        self.property_location=property_location
        self.price_per_sqm=price_per_sqm
        self.mortgage_interest=mortgage_interest

class Rent(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    property_location=orm.Column(orm.String(30),nullable=False)
    bedrooms=orm.Column(orm.Integer,nullable=False)
    monthly_price=orm.Column(orm.Float,nullable=False)
    location_id=orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique=True,nullable=False)

    def __init__(self,property_location,bedrooms,monthly_price):
        self.property_location=property_location
        self.bedrooms=bedrooms
        self.monthly_price=monthly_price

class Utilities(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    utility=orm.Column(orm.String(80),nullable=False)
    monthly_price=orm.Column(orm.Float,nullable=False)
    location_id=orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique=True,nullable=False)

    def __init__(self,utility,monthly_price):
        self.utility=utility
        self.monthly_price=monthly_price

class Transportation(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    type=orm.Column(orm.String(70),nullable=False)
    price=orm.Column(orm.Float,nullable=False)
    location_id=orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique=True,nullable=False)

    def __init__(self,type,price):
        self.type=type
        self.price=price

class Food_and_Beverage(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    item_category=orm.Column(orm.String(20),nullable=False)
    purchase_point=orm.Column(orm.String(20),nullable=False)
    item=orm.Column(orm.String(30),nullable=False)
    price=orm.Column(orm.Float,nullable=False)
    location_id=orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique=True,nullable=False)

    def __init__(self,item_category,purchase_point,item,price):
        self.item_category=item_category
        self.purchase_point=purchase_point
        self.item=item
        self.price=price

class Childcare(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    type=orm.Column(orm.String(80),nullable=False)
    annual_price=orm.Column(orm.Float,nullable=False)
    location_id=orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique=True,nullable=False)

    def __init__(self,type,annual_price):
        self.type=type
        self.annual_price=annual_price

class Apparel(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    item=orm.Column(orm.String(70),nullable=False)
    price=orm.Column(orm.Float,nullable=False)
    location_id=orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique=True,nullable=False)

    def __init__(self,item,price):
        self.item=item
        self.price=price

class Leisure(orm.Model,ResourceAddUpdateDelete):
    id=orm.Column(orm.Integer,primary_key=True)
    activity=orm.Column(orm.String(50),nullable=False)
    price=orm.Column(orm.Float,nullable=False)
    location_id=orm.Column(orm.Integer,orm.ForeignKey('location.id'),unique=True,nullable=False)

    def __init__(self,activity,price):
        self.activity=activity
        self.price=price

class CurrencySchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    abbreviation=fields.String(required=True,validate=validate.Length(3))
    usd_to_local_exchange_rate=fields.Float(required=True)
    location=fields.Nested('LocationSchema',only=['country'],many=True)

class LocationSchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    country=fields.String(required = True)
    city=fields.String(required=True)

class Home_PurchaseSchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    location=fields.Nested(LocationSchema,required = True)
    property_location=fields.String(required=True,validate=validate.Length(10))
    price_per_sqm=fields.Float(required = True)
    mortgage_interest=fields.Float(required = True)

class RentSchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    location=fields.Nested(LocationSchema,required = True)
    property_location=fields.String(required=True,validate=validate.Length(10))
    bedrooms=fields.Float(required = True)
    monthly_price=fields.Float(required = True)

class UtilitiesSchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    location=fields.Nested(LocationSchema,required = True)
    utility=fields.String(required=True)
    monthly_price=fields.Float(required = True)

class TransportationSchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    location=fields.Nested(LocationSchema,required = True)
    type=fields.String(required = True)
    price=fields.Float(required = True)

class Food_and_BeverageSchema(ma.Schema):
    id=fields.Integer(dumpy_only=True)
    location=fields.Nested(LocationSchema,required = True)
    item_category=fields.String(required=True)
    purchase_point=fields.String(required=True)
    item=fields.String(required = True)
    price=fields.Float(required = True)

class ChildcareSchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    location=fields.Nested(LocationSchema,required = True)
    type=fields.String(required=True)
    annual_price=fields.Float(required = True)

class ApparelSchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    location=fields.Nested(LocationSchema,required = True)
    item=fields.String(required=True)
    price=fields.Float(required = True)

class LeisureSchema(ma.Schema):
    id=fields.Integer(dump_only=True)
    location=fields.Nested(LocationSchema,required = True)
    activity=fields.String(dump_only=True)
    price=fields.Float(required = True)








