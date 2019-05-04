from ..extensions import db
from flask_login import UserMixin as FlaskLoginUser


class Voter(db.Model, FlaskLoginUser):
    """ Implements a Voter class that can be accessed by flask-login and
        handled by flask-sqlalchemy. Any human has a unique Voter object for
        each election in which they are a voter. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    email = db.Column(db.Text)
    email_confirmed = db.Column(db.Boolean)
    phone = db.Column(db.Text)
    phone_confirmed = db.Column(db.Boolean)
    pw_hash = db.Column(db.Text)
    salt = db.Column(db.Text)

    def __init__(self, name, email, pw_hash, salt):
        self.name = name
        self.email = email
        self.pw_hash = pw_hash
        self.salt = salt

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<Voter {self.id} ({self.name})>'
