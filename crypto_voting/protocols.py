#!/usr/bin/env python3
"""
protocols.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains main protocols for the ShuffleSum voting algorithm.

"""

from crypto_voting.crypto import EncryptedNumber, PrivateKey, PublicKey

from crypto_voting.ballots import PreferenceOrderBallot, FirstPreferenceBallot, CandidateOrderBallot, CandidateEliminationBallot

def eliminate_candidate_set(candidate_set: List[int], ballots: List[CandidateOrderBallot], private_key: PrivateKey, public_key: PublicKey):
    """ Eliminate the given candidate set. """
    # Deal with an empty set of ballots, just in case
    if len(ballots) == 0:
        return []
    # The number of remaining candidates (note that they not necessarily have numbers 1 through m)
    m = len(ballots[0].candidates)
    eliminated = [1 if ballots[0].candidates[i] in candidate_set else 0 for i in range(m)]
    relevant_columns = []
    for i in range(m):
        if eliminated[i] == 1:
            relevant_columns.append(i)
    result = []
    for ballot in ballots:
        ceb = ballot.to_candidate_elimination(eliminated, private_key, public_key)
        prefix_sum = public_key.encrypt(0)
        for i in range(m):
            prefix_sum += ceb.eliminated[i]
            ceb.preferences[i] -= prefix_sum
        cob = ceb.to_candidate_order(private_key, public_key)
        updated_candidates = [cob.candidates[i] for i in relevant_columns]
        updated_preferences = [cob.preferences[i] for i in relevant_columns]
        result.append(CandidateOrderBallot(updated_candidates, updated_preferences, cob.weight))
    return result