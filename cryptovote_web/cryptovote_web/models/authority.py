from ..extensions import db
from flask_login import UserMixin as FlaskLoginUser


class Authority(db.Model, FlaskLoginUser):
    """ Implements an Authority class that can be accessed by flask-login and
        handled by flask-sqlalchemy. Any human has a unique Authority object
        for each election in which they are an authority. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    email = db.Column(db.Text)
    email_confirmed = db.Column(db.Boolean)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)

    ukey = db.Column(db.String(20), unique=True, nullable=False)
    credential_id = db.Column(db.String(250), unique=True, nullable=False)
    pub_key = db.Column(db.String(65), unique=True, nullable=True)
    sign_count = db.Column(db.Integer, default=0)
    rp_id = db.Column(db.String(253), nullable=False)
    icon_url = db.Column(db.String(2083), nullable=False)

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<Authority {self.id} ({self.name})>'
