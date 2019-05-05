"""Extensions module - Set up for additional libraries can go in here."""

from flask_sqlalchemy import SQLAlchemy
from os import urandom, makedirs
from os.path import join, isdir, dirname
from flask_login import LoginManager

# Initialize database object
db = SQLAlchemy()

# Initialize user manager
login_manager = LoginManager()


def install_secret_key(app, filename='secret.key'):
    """ Configure the SECRET_KEY from a file in the
    instance directory. If the file does not exist,
    generate a random key, and save it. """
    filename = join(app.instance_path, filename)
    try:
        app.config['SECRET_KEY'] = open(filename, 'rb').read()
    except IOError:
        if not isdir(dirname(filename)):
            makedirs(dirname(filename))
        with open(filename, 'wb+') as f:
            f.write(urandom(64))
        app.config['SECRET_KEY'] = open(filename, 'rb').read()
        print("Generated Random Secret Key")


def title(value):
    """ Title cases a string, replacing hyphens with spaces """
    return value.replace('-', ' ').title()
