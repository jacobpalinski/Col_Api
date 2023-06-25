from flask import Flask, current_app
from flask_migrate import Migrate
from models import orm
from sqlalchemy import create_engine
from views import cost_of_living_blueprint
from flasgger import Swagger

# Create api based on config.py
def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)
    app.config['SWAGGER'] = {
        'title': "Cost of Living API",
        'uiversion': 3
    }
    orm.init_app(app)
    app.register_blueprint(cost_of_living_blueprint,url_prefix='/v1/cost-of-living')
    migrate = Migrate(app,orm)
    swagger = Swagger(app)
    return app

app = create_app('config')