""" Miscellaneous helper functions """
import random
import string
from .models.election import Election
from functools import wraps
from flask import url_for, redirect


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


def election_exists(f):
    """ Verifies that an election exists and redirects to home otherwise.
        Requires that the election name is the first argument to the
        function. Should be applied after @blueprint.route() """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'election' not in kwargs:
            return redirect(url_for('home.index'))
        election_data = Election.query.filter_by(name=kwargs['election']).first()
        if not election_data:
            return redirect(url_for('home.index'))
        return f(*args, **kwargs)
    return decorated
