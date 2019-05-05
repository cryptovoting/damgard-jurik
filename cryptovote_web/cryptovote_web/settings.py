"""Settings configuration - Configuration for environment variables can go in here."""

import os
from dotenv import load_dotenv

# Load the .env file into the environment
load_dotenv()

# Ensure that a .env file was loaded
if os.getenv('DATABASE_URL') is None:
    raise NameError("Some environment variables not defined. "
                    "Have you created a .env file?")

# Load variables from environment
ENV = os.getenv('FLASK_ENV', default='production')
DEBUG = ENV == 'development'
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SERVER_NAME = os.getenv('SERVER_NAME')
