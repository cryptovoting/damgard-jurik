from ..extensions import db


class Candidate(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'),
                            nullable=False)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f'<Candidate {self.id} ({self.name})>'
