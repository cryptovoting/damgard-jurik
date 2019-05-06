from ..extensions import db
from flask_login import UserMixin as FlaskLoginUser
from uuid import uuid4


class Authority(db.Model, FlaskLoginUser):
    """ Implements an Authority class that can be accessed by flask-login and
        handled by flask-sqlalchemy. Any human has a unique Authority object
        for each election in which they are an authority. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    email_key = db.Column(db.Text, unique=True, nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'),
                            nullable=False)

    ukey = db.Column(db.String(20), unique=True, nullable=False)
    credential_id = db.Column(db.String(250), unique=True, nullable=False)
    pub_key = db.Column(db.String(65), unique=True, nullable=True)
    sign_count = db.Column(db.Integer, default=0)
    rp_id = db.Column(db.String(253), nullable=False)
    icon_url = db.Column(db.String(2083), nullable=False)

    def __init__(self, **kwargs):
        self.email_key = str(uuid4())
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<Authority {self.id} ({self.name})>'
