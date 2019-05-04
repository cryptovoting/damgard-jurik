# Used for deploying on Apache with mod_wsgi
from cryptovote_web.app import create_app
application = create_app()
