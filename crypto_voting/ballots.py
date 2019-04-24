#!/usr/bin/env python3
"""
ballots.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains class definitions for the different ballot representations
used in the ShuffleSum voting algorithm, including:
- Preference Order Ballots
- First Preference Ballots
- Candidate Order Ballots
- Candidate Elimination Ballots

"""
from abc import ABC
from typing import List
from secrets import randbelow

from crypto_voting.crypto import EncryptedNumber, PrivateKey, PublicKey


class Ballot(ABC):
    """ Abstract class for all ballots """

    def shuffle(*rows):
        """ Given some number of lists, performs the same random element-wise
            permutation on each list. Useful for shuffling columns in
            ShuffleSum.

            Example usage:
                candidates,preferences,weights = shuffle(candidates, preferences, weights)
        """
        columns = list(zip(*rows))
        # Perform a Fisher-Yates shuffle using cryptographically secure randomness
        n = len(columns)
        for i in range(n-1):
            # i <= j < n
            j = randbelow(n-i) + i
            columns[i], columns[j] = columns[j], columns[i]
        # Return translation of columns back to rows
        return [list(t) for t in zip(*columns)]


class PreferenceOrderBallot(Ballot):
    """ The voter orders the candidades by preference.
        Preferences are known, candidates are hidden. """
    def __init__(self, candidates: List[EncryptedNumber], preferences: List[int], weight: EncryptedNumber):
        self.candidates = candidates
        self.preferences = preferences
        self.weight = weight


class FirstPreferenceBallot(Ballot):
    """ Ballot in candidate order with encrypted weight for each candidate. """
    def __init__(self, candidates: List[int], weights: List[EncryptedNumber]):
        self.candidates = candidates
        self.weights = weights


class CandidateOrderBallot(Ballot):
    """ The voter orders the canditades by preference.
        Preferences are hidden, candidates are known. """
    def __init__(self, candidates: List[int], preferences: List[EncryptedNumber], weight: EncryptedNumber):
        self.candidates = candidates
        self.preferences = preferences
        self.weight = weight


class CandidateEliminationBallot(Ballot):
    """ Ballot in preference order with encrypted candidates and encrypted
        binary elimination vector. """
    def __init__(self, candidates: List[int], preferences: List[EncryptedNumber], eliminated: List[EncryptedNumber]):
        self.candidates = candidates
        self.preferences = preferences
        self.eliminated = eliminated


def candidate_order_to_first_preference(ballot: CandidateOrderBallot, private_key: PrivateKey, public_key: PublicKey) -> FirstPreferenceBallot:
    """ Converts a candidate order ballot into a first preference ballot. """
    # Initialization
    n = len(ballot.candidates)
    candidates = ballot.candidates
    preferences = ballot.preferences
    weight = ballot.weight
    # Step 1: Encrypt the candidate row
    candidates = [public_key.encrypt(candidate) for candidate in candidates]
    # Step 2: Shuffle the table columns (TO-DO)
    candidates, preferences = ballot.shuffle(candidates, preferences)
    # Step 3: Threshold decrypt the preference row
    preferences = [private_key.decrypt(preference) for preference in preferences]
    # Step 4: Sort columns in preference order
    tmp = [(preferences[i], candidates[i]) for i in range(n)]
    tmp.sort()
    preferences = [tmp[i][0] for i in range(n)]
    candidates = [tmp[i][1] for i in range(n)]
    # Step 5: Add a weights row
    weights = [public_key.encrypt(0) for i in range(n)]
    weights[0] = public_key.encrypt(weight)
    # Step 6: Encrypt the preference row
    preferences = [public_key.encrypt(preference) for preference in preferences]
    # Step 7: Shuffle the table columns (TO-DO)
    candidates, weights = ballot.shuffle(candidates, weights)
    # Step 8: Threshold decrypt the candidate row
    candidates = [private_key.decrypt(candidate) for candidate in candidates]
    # Step 9: Sort columns in candidate order
    tmp = [(candidate[i], weights[i]) for i in range(n)]
    candidates = [tmp[i][0] for i in range(n)]
    weights = [tmp[i][1] for i in range(n)]
    # Return the result
    return FirstPreferenceBallot(candidates, weights)


def candidate_order_to_candidate_elimination(ballot: CandidateOrderBallot, eliminated: List[int], private_key: PrivateKey, public_key: PublicKey, ) -> CandidateEliminationBallot:
    """ Converts a candidate order ballot into a candidate elimination ballot.
        Assumes eliminated is a list of either 0 or 1, *unencrypted*. """
    # Initialization
    n = len(ballot.candidates)
    candidates = ballot.candidates
    preferences = ballot.preferences
    weight = ballot.weight
    # Step 1: Add an elimination-tag row to the ballot
    eliminated = [public_key.encrypt(eliminated[i]) for i in range(n)]
    # Step 2: Encrypt the candidate row
    candidates = [public_key.encrypt(candidate) for candidate in candidates]
    # Step 3: Shuffle the table columns (TO-DO)
    candidates, preferences, eliminated = ballot.shuffle(candidates, preferences, eliminated)
    # Step 4: Threshold decrypt the preference row
    preferences = [private_key.decrypt(preference) for preference in preferences]
    # Step 5: Sort the table columns by preference
    tmp = [(preferences[i], candidates[i], eliminated[i]) for i in range(n)]
    tmp.sort()
    preferences = [tmp[i][0] for i in range(n)]
    candidates = [tmp[i][1] for i in range(n)]
    eliminated = [tmp[i][2] for i in range(n)]
    # Step 6: Encrypt the preference row
    preferences = [private_key.encrypt(preference) for preference in preferences]
    # Return the result
    return CandidateEliminationBallot(candidates, preferences, eliminated)

def candidate_elimination_to_candidate_order(ballot: CandidateEliminationBallot, private_key: PrivateKey, public_key: PublicKey) -> CandidateOrderBallot:
    """ Converts a candidate elimination ballot into a candidate order ballot. """
    raise NotImplementedError