from flask import Flask
from flask_migrate import Migrate
from views import cost_of_living_blueprint
from models import orm

def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)
    orm.init_app(app)
    app.register_blueprint(cost_of_living_blueprint,prefix='/costofliving')
    migrate = Migrate(app,orm)
    return app

app = create_app('config')