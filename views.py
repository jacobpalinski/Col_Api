from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource
from httpstatus import HttpStatus
from models import (orm, ma, Currency, CurrencySchema, Location, LocationSchema, 
Home_Purchase, Home_PurchaseSchema, Rent, RentSchema, Utilities, UtilitiesSchema,
Transportation, TransportationSchema, Food_and_Beverage, Food_and_BeverageSchema,
Childcare, ChildcareSchema, Apparel, ApparelSchema, Leisure, LeisureSchema)
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

class CurrencyListResource(Resource):
    def get():
        currencies = Currency.query.all()
        dumped_currencies = currency_schema.dump(currencies,many = True)
        return dumped_currencies

class LocationListResource(Resource):
    def get():
        locations = Location.query.all()
        dumped_locations = location_schema.dump(locations,many = True)
        return dumped_locations

class LocationListResource(Resource):
    pass

class Home_Purchase_Resource(Resource):
    def get(self,country=None,city=None,abbreviation=None):

        if None not in (country,city,abbreviation):
            home_purchase = Home_Purchase.query.join(Location, 
            Home_Purchase.location_id == Location.id)\
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
            home_purchase = Home_Purchase.query.join(Location, 
            Home_Purchase.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Home_Purchase.property_location.asc(),Home_Purchase.price_per_sqm.asc()).all().get_or_404()
            dumped_home_purchase = home_purchase_schema.dump(home_purchase,many = True)
            return dumped_home_purchase

class Rent_Resource(Resource):
    def get(self,country=None,city=None,abbreviation=None):

        if None not in (country,city,abbreviation):
            rent = Rent.query.join(Location, 
            Rent.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Rent.bedrooms.asc()).all().get_or_404()
            dumped_rent = rent_schema.dump(rent,many = True)
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
            rent = Rent.query.join(Location, 
            Rent.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Rent.bedrooms.asc(),Rent.monthly_price.asc()).all().get_or_404()
            dumped_rent = home_purchase_schema.dump(rent,many = True)
            return dumped_rent

class Utilities_Resource(Resource):
    def get(self,country=None,city=None,abbreviation=None):

        if None not in (country,city,abbreviation):
            utilities = Utilities.query.join(Location, 
            Utilities.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Utilities.utility.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities,many = True)
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
            utilities = Utilities.query.join(Location, 
            Utilities.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Utilities.utility.asc(),Utilities.monthly_price.asc()).all().get_or_404()
            dumped_utilities = utilities_schema.dump(utilities,many = True)
            return dumped_utilities


class Transportation_Resource(Resource):
    def get(self,country=None,city=None,abbreviation=None):

        if None not in (country,city,abbreviation):
            transportation = Transportation.query.join(Location, 
            Transportation.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Transportation.type.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation,many = True)
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
            transportation = Transportation.query.join(Location, 
            Transportation.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Transportation.type.asc(),Transportation.price.asc()).all().get_or_404()
            dumped_transportation = transportation_schema.dump(transportation,many = True)
            return dumped_transportation

class Food_and_Beverage_Resource(Resource):
    def get(self,country=None,city=None,abbreviation=None):

        if None not in (country,city,abbreviation):
            food_and_beverage = Food_and_Beverage.query.join(Location, 
            Food_and_Beverage.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage,many = True)
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
            food_and_beverage = Food_and_Beverage.query.join(Location, 
            Food_and_Beverage.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Food_and_Beverage.item_category.asc(),
            Food_and_Beverage.purchase_point.asc(),Food_and_Beverage.price.asc()).all().get_or_404()
            dumped_food_and_beverage = food_and_beverage_schema.dump(food_and_beverage,many = True)
            return dumped_food_and_beverage

class Childcare_Resource(Resource):
    def get(self,country=None,city=None,abbreviation=None):

        if None not in (country,city,abbreviation):
            childcare = Childcare.query.join(Location, 
            Childcare.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Childcare.type.asc()).all().get_or_404()
            dumped_childcare = childcare_schema.dump(childcare,many = True)
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
            childcare = Childcare.query.join(Location, 
            Childcare.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Childcare.type.asc(), Childcare.annual_price.asc()).all().get_or_404()
            dumped_childcare = childcare_schema.dump(childcare,many = True)
            return dumped_childcare

class Apparel_Resource(Resource):
    def get(self,country=None,city=None,abbreviation=None):

        if None not in (country,city,abbreviation):
            apparel = Apparel.query.join(Location, 
            Apparel.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Apparel.item.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel,many = True)
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
            apparel = Apparel.query.join(Location, 
            Apparel.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Apparel.item.asc(),Apparel.price.asc()).all().get_or_404()
            dumped_apparel = apparel_schema.dump(apparel,many = True)
            return dumped_apparel

class Leisure_Resource(Resource):
    def get(self,country=None,city=None,abbreviation=None):

        if None not in (country,city,abbreviation):
            leisure = Leisure.query.join(Location, 
            Leisure.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Location.country == country,
            Location.city == city, Currency.abbreviation == abbreviation)\
            .order_by(Leisure.activity.asc()).all().get_or_404()
            dumped_leisure = leisure_schema.dump(leisure,many = True)
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
            leisure = Leisure.query.join(Location, 
            Leisure.location_id == Location.id)\
            .join(Currency, Location.id==Currency.id).filter(Currency.abbreviation == abbreviation)\
            .order_by(Leisure.activity.asc(),Leisure.price.asc()).all().get_or_404()
            dumped_leisure = leisure_schema.dump(leisure,many = True)
            return dumped_leisure

        


        
        
cost_of_living.add_resource(CurrencyListResource, '/currencies/')
cost_of_living.add_resource(LocationListResource, '/locations/')
cost_of_living.add_resource(Home_Purchase_Resource,'/homepurchase/<string:country>/<string:city>/\
<string:abbreviation>')
cost_of_living.add_resource(Rent_Resource,'/rent/<string:country>/<string:city>/\
<string:abbreviation>')
cost_of_living.add_resource(Utilities_Resource,'/utilites/<string:country>/<string:city>/\
<string:abbreviation>')
cost_of_living.add_resource(Transportation_Resource,'/transportation/<string:country>/<string:city>/\
<string:abbreviation>')
cost_of_living.add_resource(Food_and_Beverage_Resource,'/foodbeverage/<string:country>/<string:city>/\
<string:abbreviation>')
cost_of_living.add_resource(Childcare_Resource,'/childcare/<string:country>/<string:city>/\
<string:abbreviation>')
cost_of_living.add_resource(Apparel_Resource,'/apparel/<string:country>/<string:city>/\
<string:abbreviation>')
cost_of_living.add_resource(Leisure_Resource,'/leisure/<string:country>/<string:city>/\
<string:abbreviation>')
