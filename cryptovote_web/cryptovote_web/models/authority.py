from ..extensions import db
from flask_login import UserMixin as FlaskLoginUser
from uuid import uuid4
from cryptovote.damgard_jurik import keygen


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
    public_key = db.Column(db.PickleType, unique=True, nullable=False)
    private_key_ring = db.Column(db.PickleType, nullable=False)

    webauthn = db.Column(db.Boolean, nullable=False)
    ukey = db.Column(db.String(20), unique=True, nullable=True)
    credential_id = db.Column(db.String(250), unique=True, nullable=True)
    pub_key = db.Column(db.String(65), unique=True, nullable=True)
    sign_count = db.Column(db.Integer, default=0)
    rp_id = db.Column(db.String(253), nullable=True)
    icon_url = db.Column(db.String(2083), nullable=True)

    pw_hash = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        self.email_key = str(uuid4())
        keypair = keygen(threshold=1, n_shares=1, n_bits=32)
        self.public_key = keypair[0]
        self.private_key_ring = keypair[1]
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<Authority {self.id} ({self.name})>'
