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

from crypto import Ciphertext, Plaintext

class Ballot(ABC):
    """ Abstract class for all ballots """
    pass


class PreferenceOrderBallot(Ballot):
    """ The voter orders the canditades by preference.
        Preferences are known, candidates are hidden """"
    def __init__(self, candidates: List[Ciphertext], preferences: List[Plaintext], weight: Ciphertext):
        self.candidates = candidates
        self.preferences = preferences
        self.weight = weight


class CandidateOrderBallot(Ballot):
    """ The voter orders the canditades by preference.
        Preferences are hidden, candidates are known """"
    def __init__(self, candidates: List[Plaintext], preferences: List[Ciphertext], weight: Ciphertext):
        self.candidates = candidates
        self.preferences = preferences
        self.weight = weight

    def to_first_preference(self) -> FirstPreferenceBallot:
        raise NotImplementedError

    def to_candidate_elimination(self) -> CandidateEliminationBallot:
        raise NotImplementedError

class FirstPreferenceBallot(Ballot):
    """ Ballot in candidate order with encrypted weight for each candidate. """
    def __init__(self, candidates: List[Plaintext], weights: List[Ciphertext]):
        self.candidates = candidates
        self.weights = weights

class CandidateEliminationBallot(Ballot):
    """ Ballot in preference order with encrypted candidates and encrypted
        binary elimination vector. """
    def __init__(self, candidates: List[Plaintext], preferences: List[Ciphertext], eliminated: List[Ciphertext]):
        self.candidates = candidates
        self.preferences = preferences
        self.eliminated = eliminated

    def to_candidate_order(self) -> CandidateOrderBallot:
        raise NotImplementedError
