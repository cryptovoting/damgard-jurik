"""Extensions module - Set up for additional libraries can go in here."""
import random
import string
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


def generate_challenge(challenge_len):
    """ Used in webauthn """
    return ''.join([
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for i in range(challenge_len)
    ])


def generate_ukey():
    """ Used in webauthn
        Its value's id member is required, and contains an identifier
        for the account, specified by the Relying Party. This is not meant
        to be displayed to the user, but is used by the Relying Party to
        control the number of credentials - an authenticator will never
        contain more than one credential for a given Relying Party under
        the same id.

        A unique identifier for the entity. For a relying party entity,
        sets the RP ID. For a user account entity, this will be an
        arbitrary string specified by the relying party. """
    return generate_challenge(20)


def title(value):
    """ Title cases a string, replacing hyphens with spaces """
    return value.replace('-', ' ').title()
