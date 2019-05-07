from ..extensions import db
from uuid import uuid4


class UnconfirmedAuthority(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    election_name = db.Column(db.Text)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    email_key = db.Column(db.Text, unique=True, nullable=False)

    def __init__(self, **kwargs):
        self.email_key = str(uuid4())
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<UnconfirmedAuthority {self.id} ({self.name})>'
