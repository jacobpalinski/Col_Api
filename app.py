from flask import Flask, current_app
from flask_migrate import Migrate
from models import orm
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from views import cost_of_living_blueprint

def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)
    orm.init_app(app)
    app.register_blueprint(cost_of_living_blueprint,prefix='/costofliving')
    migrate = Migrate(app,orm)
    return app

app = create_app('config')