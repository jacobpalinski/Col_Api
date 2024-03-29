# Configuration settings for testing
import os

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:Databrah91@localhost:5432/test_cost_of_living"
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
PAGINATION_PAGE_SIZE = 50
PAGINATION_PAGE_ARGUMENT_NAME = 'page'
TESTING = True
WTF_CSRF_ENABLED = False
SERVER_NAME = "127.0.0.1"
