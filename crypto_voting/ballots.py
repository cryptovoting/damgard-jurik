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

from crypto_voting.crypto import EncryptedNumber


class Ballot(ABC):
    """ Abstract class for all ballots """
    pass


class PreferenceOrderBallot(Ballot):
    """ The voter orders the canditades by preference.
        Preferences are known, candidates are hidden. """
    def __init__(self, candidates: List[EncryptedNumber], preferences: List[int], weight: Ciphertext):
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


def candidate_order_to_first_preference(ballot: CandidateOrderBallot) -> FirstPreferenceBallot:
    raise NotImplementedError


def candidate_order_to_candidate_elimination(ballot: CandidateOrderBallot) -> CandidateEliminationBallot:
    raise NotImplementedError


def candidate_elimination_to_candidate_order(ballot: CandidateEliminationBallot) -> CandidateOrderBallot:
    raise NotImplementedError
