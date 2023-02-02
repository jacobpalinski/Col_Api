import os

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = True
# Replace your_user_name with the user name you configured for the database
# Replace your_password with the password you specified for the database
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:Databrah91@5432/cost_of_living"
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
PAGINATION_PAGE_SIZE = 50
PAGINATION_PAGE_ARGUMENT_NAME = 'page'
