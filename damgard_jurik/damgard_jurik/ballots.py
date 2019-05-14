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

from cryptovote.damgard_jurik import EncryptedNumber, PrivateKeyRing, PublicKey


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
        return [list(col) for col in zip(*columns)]

    @staticmethod
    def sort(*rows):
        """ Given some number of lists, sorts all of them according to the
            sorting of the first list.

            Example usage:
                candidates,preferences,weights = sort(candidates, preferences, weights)
                # All three lists are sorted according to the sorting of candidates
        """
        columns = list(zip(*rows))
        columns.sort()  # Note: Python sorts based on the first element of a tuple
        return [list(col) for col in zip(*columns)]


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


class CandidateEliminationBallot(Ballot):
    """ Ballot in preference order with encrypted candidates and encrypted
        binary elimination vector. """

    def __init__(self,
                 candidates: List[EncryptedNumber],
                 preferences: List[EncryptedNumber],
                 eliminated: List[EncryptedNumber],
                 weight: EncryptedNumber):
        self.candidates = candidates
        self.preferences = preferences
        self.eliminated = eliminated
        self.weight = weight


def candidate_order_to_first_preference(ballot: CandidateOrderBallot,
                                        private_key_ring: PrivateKeyRing,
                                        public_key: PublicKey) -> FirstPreferenceBallot:
    """ Converts a candidate order ballot into a first preference ballot. """
    # Initialization
    n = len(ballot.candidates)
    candidates = ballot.candidates
    preferences = ballot.preferences
    weight = ballot.weight

    # Step 1: Encrypt the candidate row
    candidates = public_key.encrypt_list(candidates)

    # Step 2: Shuffle the table columns
    candidates, preferences = ballot.shuffle(candidates, preferences)

    # Step 3: Threshold decrypt the preference row
    preferences = private_key_ring.decrypt_list(preferences)

    # Step 4: Sort columns in preference order
    preferences, candidates = ballot.sort(preferences, candidates)

    # Step 5: Add a weights row
    weights = [weight] + public_key.encrypt_list([0] * (n - 1))

    # Step 6: Encrypt the preference row
    preferences = public_key.encrypt_list(preferences)

    # Step 7: Shuffle the table columns
    candidates, preferences, weights = ballot.shuffle(candidates, preferences, weights)

    # Step 8: Threshold decrypt the candidate row
    candidates = private_key_ring.decrypt_list(candidates)

    # Step 9: Sort columns in candidate order
    candidates, preferences, weights = ballot.sort(candidates, preferences, weights)

    # Return the result
    return FirstPreferenceBallot(candidates, preferences, weights)


def candidate_order_to_candidate_elimination(ballot: CandidateOrderBallot,
                                             eliminated: List[int],
                                             private_key_ring: PrivateKeyRing,
                                             public_key: PublicKey) -> 'CandidateEliminationBallot':
    """ Converts a candidate order ballot into a candidate elimination ballot.
        Assumes eliminated is a list of either 0 or 1, *unencrypted*. """
    # Initialization
    n = len(ballot.candidates)
    candidates = ballot.candidates
    preferences = ballot.preferences
    weight = ballot.weight

    # Step 1: Add an elimination-tag row to the ballot
    eliminated = public_key.encrypt_list(eliminated,)

    # Step 2: Encrypt the candidate row
    candidates = public_key.encrypt_list(candidates)

    # Step 3: Shuffle the table columns
    candidates, preferences, eliminated = ballot.shuffle(candidates, preferences, eliminated)

    # Step 4: Threshold decrypt the preference row
    preferences = private_key_ring.decrypt_list(preferences)

    # Step 5: Sort the table columns by preference
    preferences, candidates, eliminated = ballot.sort(preferences, candidates, eliminated)

    # Step 6: Encrypt the preference row
    preferences = public_key.encrypt_list(preferences)

    # Return the result
    return CandidateEliminationBallot(candidates, preferences, eliminated, weight)


def candidate_elimination_to_candidate_order(ballot: CandidateEliminationBallot,
                                             private_key_ring: PrivateKeyRing) -> CandidateOrderBallot:
    """ Converts a candidate elimination ballot into a candidate order ballot. """
    # Initialization
    candidates = ballot.candidates
    preferences = ballot.preferences
    weight = ballot.weight

    # Step 1: Shuffle the table columns
    candidates, preferences = ballot.shuffle(candidates, preferences)

    # Step 2: Threshold decrypt the candidate row
    candidates = private_key_ring.decrypt_list(candidates)

    # Step 3: Sort the table columns by candidate
    candidates, preferences = ballot.sort(candidates, preferences)

    # Return the result
    return CandidateOrderBallot(candidates, preferences, weight)
