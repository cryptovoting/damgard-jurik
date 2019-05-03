"""Extensions module - Set up for additional libraries can go in here."""
from flask_sqlalchemy import SQLAlchemy
from os import urandom, makedirs
from os.path import join, isdir, dirname

db = SQLAlchemy()


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
        print("Generated Random Secret Key")
