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
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<Voter {self.id} ({self.name})>'
