from ..extensions import db


class Election(db.Model):
    """ Implements an object to represent all data relating to a specific
        election """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    voters = db.relationship('Voter',
                             backref=db.backref('election', lazy='joined'),
                             lazy=True)
    authorities = db.relationship('Authority',
                                  backref=db.backref('election', lazy='joined'),
                                  lazy=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'<Election {self.id} ({self.name})>'
