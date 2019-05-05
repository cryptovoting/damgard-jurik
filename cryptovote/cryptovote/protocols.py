#!/usr/bin/env python3
"""
protocols.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains main protocols for the ShuffleSum voting algorithm.

"""

from typing import List

from cryptovote.ballots import PreferenceOrderBallot, FirstPreferenceBallot, CandidateOrderBallot, CandidateEliminationBallot
from cryptovote.crypto import EncryptedNumber, PrivateKey, PublicKey
from cryptovote.utils import lcm


def eliminate_candidate_set(candidate_set: List[int], ballots: List[CandidateOrderBallot], private_key: PrivateKey, public_key: PublicKey) -> List[CandidateOrderBallot]:
    """ Eliminate the given candidate set (1d) """
    # Deal with an empty set of ballots, just in case
    if len(ballots) == 0:
        return []
    # The number of remaining candidates (note that they not necessarily have numbers 1 through m)
    m = len(ballots[0].candidates)
    eliminated = [1 if ballots[0].candidates[i] in candidate_set else 0 for i in range(m)]
    relevant_columns = set() # holds non eliminated candidates
    for i in range(m):
        if eliminated[i] == 0:
            relevant_columns.add(i)
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


def compute_first_preference_tallies(ballots: List[CandidateOrderBallot], private_key: PrivateKey, public_key: PublicKey) -> (List[FirstPreferenceBallot], List[int]):
    """ Compute First-Preference Tallies (1b)
        Assumes there is at least one ballot.   """
    # Initialization
    m = len(ballots[0].candidates)
    encrypted_tallies = [public_key.encrypt(0) for i in range(m)]
    # Perform computation
    fpb_ballots = []
    for ballot in ballots:
        fpb = ballot.to_first_preference(private_key, public_key)
        fpb_ballots.append(fpb)
        for i in range(m):
            encrypted_tallies[i] += fpb.weights[i]
    # Return the result
    return fpb_ballots, [private_key.decrypt(encrypted_tally) for encrypted_tally in encrypted_tallies]


def reweight_votes(ballots: List[FirstPreferenceBallot], elected: List[int], q: int, t: List[int], private_key: PrivateKey, public_key: PublicKey) -> List[CandidateOrderBallot]:
    """ Reweight the votes for elected candidates in S with quota q. """
    if len(ballots) == 0:
        raise ValueError
    candidates = ballots[0].candidates
    m = len(candidates)
    d_lcm = 1
    for i in range(m):
        # only consider the elected candidates
        if candidates[i] not in elected:
            continue
        d_lcm = lcm(d_lcm, t[i])
    result = []
    for ballot in ballots:
        new_weight = public_key.encrypt(0)
        for i in range(m):
            ballot.weights[i] *= d_lcm
            if candidates[i] in elected:
                ballot.weights[i] *= t[i]-q
                ballot.weights[i] /= t[i]
            new_weight += ballot.weights[i]
        result.append(CandidateOrderBallot(ballot.candidates, ballot.preferences, new_weight))
    return result


def stv_tally(ballots: List[CandidateOrderBallot], seats: int, private_key: PrivateKey, public_key: PublicKey) -> List[int]:
    """ The main protocol of the ShuffleSum voting algorithm.
        Assumes there is at least one ballot.
        Returns a list of elected candidates. """
    if len(ballots) == 0:
        raise ValueError
    c_rem = ballots[0].candidates       # the remaining candidates
    q = len(ballots)//(seats+1) + 1     # the quota required for election
    result = []
    while len(c_rem) > seats:
        fpb_ballots, t = compute_first_preference_tallies(ballots, private_key, public_key)
        elected = []
        for i in range(len(c_rem)):
            if t[i] >= q:               # TODO NOTE: Not sure if it needs to be >= or >
                elected.append(ballots[0].candidates[i])
        if len(elected) > 0:
            result += elected
            ballots = reweight_votes(fpb_ballots, elected, q, t, private_key, public_key)
            ballots = eliminate_candidate_set(elected, ballots, private_key, public_key)
        else:
            i = 0
            for j in range(len(c_rem)):
                if t[j] < t[i]:
                    i = j
            ballots = eliminate_candidate_set([i], ballots, private_key, public_key)
        c_rem = ballots[0].candidates
    return result
