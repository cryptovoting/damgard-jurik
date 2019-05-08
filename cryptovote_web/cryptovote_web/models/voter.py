from ..extensions import db
from uuid import uuid4


class Voter(db.Model):
    """ Any human has a unique Voter object for each election in which
        they are a voter. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    email = db.Column(db.Text, nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    email_key = db.Column(db.Text, unique=True, nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'),
                            nullable=False)
    ballot = db.Column(db.PickleType)  # CandidateOrderBallot

    def __init__(self, **kwargs):
        self.email_key = str(uuid4())
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<Voter {self.id} ({self.name})>'
