"""Settings configuration - Configuration for environment variables can go in here."""

import os
from dotenv import load_dotenv
load_dotenv()

ENV = os.getenv('FLASK_ENV', default='production')
DEBUG = ENV == 'development'
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY', default='octocat')
SQLALCHEMY_TRACK_MODIFICATIONS = False
