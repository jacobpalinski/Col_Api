from httpstatus import *
from models import orm, User
from flask import make_response, request
from flask import url_for
from flask import current_app
from marshmallow import ValidationError

# Generates error statement for SQLAlchemy error
def sql_alchemy_error_response(error):
    orm.session.rollback()
    response = {'error': str(error)}
    return response, HttpStatus.bad_request_400.value

# Authenticates jwt token for get requests
def authenticate_jwt():
    auth_header = request.headers.get('Authorization')
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
            return True
        else:
            response = {'message' : resp}
            return response, HttpStatus.unauthorized_401.value
    else:
        response = {'message' : 'Provide a valid auth token'}
        return response, HttpStatus.forbidden_403.value

# Paginates output for get requests that generate a large number of results
class PaginationHelper():
    def __init__(self,request, query, resource_for_url, key_name, schema):
        self.request = request
        self.query = query
        self.resource_for_url = resource_for_url
        self.key_name = key_name
        self.schema = schema
        self.page_size = current_app.config['PAGINATION_PAGE_SIZE']
        self.page_argument_name = current_app.config['PAGINATION_PAGE_ARGUMENT_NAME']
        
    def paginate_query(self):
        # No page number, assume request requires page 1
        page_number = self.request.args.get(self.page_argument_name, 1, type=int)
        paginated_objects = self.query.paginate(
            page = page_number,
            per_page = self.page_size,
            error_out = False
        )
        objects = paginated_objects.items
        if paginated_objects.has_prev:
            # Formatting of previous page url based on arguments provided
            if self.request.args.get('country') and not self.request.args.get('abbreviation'):
                previous_page_url = url_for(self.resource_for_url,country=self.request.args.get('country'),page = page_number - 1, _external = True)
            elif self.request.args.get('abbreviation') and not self.request.args.get('country'):
                previous_page_url = url_for(self.resource_for_url,abbreviation=self.request.args.get('abbreviation'),page = page_number - 1, _external = True)
            elif self.request.args.get('abbreviation') and self.request.args.get('country'):
                previous_page_url = url_for(self.resource_for_url,country=self.request.args.get('country'),abbreviation=self.request.args.get('abbreviation'),page = page_number - 1, _external = True)
            else:
                previous_page_url = url_for(self.resource_for_url, page = page_number - 1, _external = True)
        else:
            previous_page_url = None

        if paginated_objects.has_next:
            # Formatting of next page url based on arguments provided
            if self.request.args.get('country') and not self.request.args.get('abbreviation'):
                next_page_url = url_for(self.resource_for_url,country=self.request.args.get('country'),page = page_number + 1, _external = True)
            elif self.request.args.get('abbreviation') and not self.request.args.get('country'):
                next_page_url = url_for(self.resource_for_url,abbreviation=self.request.args.get('abbreviation'),page = page_number + 1, _external = True)
            elif self.request.args.get('abbreviation') and self.request.args.get('country'):
                next_page_url = url_for(self.resource_for_url,country=self.request.args.get('country'),abbreviation=self.request.args.get('abbreviation'),page = page_number + 1, _external = True)
            else:
                next_page_url = url_for(self.resource_for_url, page = page_number + 1, _external = True)
        else:
            next_page_url = None
        
        dumped_objects = self.schema.dump(objects, many = True)
        return {
            self.key_name : dumped_objects,
            'previous' : previous_page_url,
            'next' : next_page_url,
            'count': paginated_objects.total
        }
