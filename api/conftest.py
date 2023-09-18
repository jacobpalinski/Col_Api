import pytest
from app import create_app
from models import orm
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from views import cost_of_living_blueprint
from sqlalchemy import create_engine

@pytest.fixture
def application():
    app = create_app('test_config')
    with app.app_context():
        # setup
        orm.create_all()
        # run
        yield app
        # teardown
        orm.session.remove()
        orm.drop_all()

# Application client fixture to be used for tests in test_views.py
@pytest.fixture
def client(application):
    return application.test_client()
