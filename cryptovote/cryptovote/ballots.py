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

from cryptovote.damgard_jurik import EncryptedNumber, PrivateKeyShare, PublicKey, threshold_decrypt


class Ballot(ABC):
    """ Abstract class for all ballots """

    @staticmethod
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
        for i in range(n - 1):
            # i <= j < n
            j = randbelow(n - i) + i
            columns[i], columns[j] = columns[j], columns[i]
        # Return translation of columns back to rows
        return [list(t) for t in zip(*columns)]


class PreferenceOrderBallot(Ballot):
    """ The voter orders the candidades by preference.
        Preferences are known, candidates are hidden. """

    def __init__(self,
                 candidates: List[EncryptedNumber],
                 preferences: List[int],
                 weight: EncryptedNumber):
        self.candidates = candidates
        self.preferences = preferences
        self.weight = weight


class FirstPreferenceBallot(Ballot):
    """ Ballot in candidate order with encrypted weight for each candidate. """
    def __init__(self,
                 candidates: List[int],
                 preferences: List[EncryptedNumber],
                 weights: List[EncryptedNumber]):
        self.candidates = candidates
        self.preferences = preferences
        self.weights = weights


class CandidateOrderBallot(Ballot):
    """ The voter orders the canditades by preference.
        Preferences are hidden, candidates are known. """

    def __init__(self,
                 candidates: List[int],
                 preferences: List[EncryptedNumber],
                 weight: EncryptedNumber):
        self.candidates = candidates
        self.preferences = preferences
        self.weight = weight

    def to_first_preference(self,
                            private_key_shares: List[PrivateKeyShare],
                            public_key: PublicKey) -> FirstPreferenceBallot:
        """ Converts a candidate order ballot into a first preference ballot. """
        # Initialization
        n = len(self.candidates)
        candidates = self.candidates
        preferences = self.preferences
        weight = self.weight

        # Step 1: Encrypt the candidate row
        candidates = [public_key.encrypt(candidate) for candidate in candidates]

        # Step 2: Shuffle the table columns
        candidates, preferences = self.shuffle(candidates, preferences)

        # Step 3: Threshold decrypt the preference row
        preferences = [threshold_decrypt(preference, private_key_shares) for preference in preferences]

        # Step 4: Sort columns in preference order
        tmp = [(preferences[i], candidates[i]) for i in range(n)]
        tmp.sort()
        preferences = [tmp[i][0] for i in range(n)]
        candidates = [tmp[i][1] for i in range(n)]

        # Step 5: Add a weights row
        weights = [public_key.encrypt(0) for i in range(n)]
        weights[0] = weight

        # Step 6: Encrypt the preference row
        preferences = [public_key.encrypt(preference) for preference in preferences]
        # Step 7: Shuffle the table columns
        candidates, preferences, weights = self.shuffle(candidates, preferences, weights)
        # Step 8: Threshold decrypt the candidate row
        candidates = [threshold_decrypt(candidate, private_key_shares) for candidate in candidates]
        # Step 9: Sort columns in candidate order
        tmp = [(candidates[i], preferences[i], weights[i]) for i in range(n)]
        tmp.sort()
        candidates = [tmp[i][0] for i in range(n)]
        preferences = [tmp[i][1] for i in range(n)]
        weights = [tmp[i][2] for i in range(n)]
        # Return the result
        return FirstPreferenceBallot(candidates, preferences, weights)

    def to_candidate_elimination(self,
                                 eliminated: List[int],
                                 private_key_shares: List[PrivateKeyShare],
                                 public_key: PublicKey, ) -> 'CandidateEliminationBallot':
        """ Converts a candidate order ballot into a candidate elimination ballot.
            Assumes eliminated is a list of either 0 or 1, *unencrypted*. """
        # Initialization
        n = len(self.candidates)
        candidates = self.candidates
        preferences = self.preferences
        weight = self.weight
        # Step 1: Add an elimination-tag row to the ballot
        eliminated = [public_key.encrypt(eliminated[i]) for i in range(n)]
        # Step 2: Encrypt the candidate row
        candidates = [public_key.encrypt(candidate) for candidate in candidates]
        # Step 3: Shuffle the table columns
        candidates, preferences, eliminated = self.shuffle(candidates, preferences, eliminated)
        # Step 4: Threshold decrypt the preference row
        preferences = [threshold_decrypt(preference, private_key_shares) for preference in preferences]
        # Step 5: Sort the table columns by preference
        tmp = [(preferences[i], candidates[i], eliminated[i]) for i in range(n)]
        tmp.sort()
        preferences = [tmp[i][0] for i in range(n)]
        candidates = [tmp[i][1] for i in range(n)]
        eliminated = [tmp[i][2] for i in range(n)]
        # Step 6: Encrypt the preference row
        preferences = [public_key.encrypt(preference) for preference in preferences]
        # Return the result
        return CandidateEliminationBallot(candidates, preferences, eliminated, weight)


class CandidateEliminationBallot(Ballot):
    """ Ballot in preference order with encrypted candidates and encrypted
        binary elimination vector. """

    def __init__(self, candidates: List[EncryptedNumber], preferences: List[EncryptedNumber],
                 eliminated: List[EncryptedNumber], weight: EncryptedNumber):
        self.candidates = candidates
        self.preferences = preferences
        self.eliminated = eliminated
        self.weight = weight

    def to_candidate_order(self, private_key_shares: List[PrivateKeyShare]) -> CandidateOrderBallot:
        """ Converts a candidate elimination ballot into a candidate order ballot. """
        # Initialization
        n = len(self.candidates)
        candidates = self.candidates
        preferences = self.preferences
        eliminated = self.eliminated
        weight = self.weight
        # Step 1: Shuffle the table columns
        candidates, preferences, eliminated = self.shuffle(candidates, preferences, eliminated)
        # Step 2: Threshold decrypt the candidate row
        candidates = [threshold_decrypt(candidate, private_key_shares) for candidate in candidates]
        # Step 3: Sort the table columns by candidate
        tmp = [(candidates[i], preferences[i], eliminated[i]) for i in range(n)]
        tmp.sort()
        candidates = [tmp[i][0] for i in range(n)]
        preferences = [tmp[i][1] for i in range(n)]
        eliminated = [tmp[i][2] for i in range(n)]
        # Return the result
        return CandidateOrderBallot(candidates, preferences, weight)
