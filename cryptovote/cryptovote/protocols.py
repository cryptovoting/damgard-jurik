#!/usr/bin/env python3
"""
protocols.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains main protocols for the ShuffleSum voting algorithm.

"""
from functools import partial
from multiprocessing import Pool
from typing import List, Tuple

from gmpy2 import mpz
from tqdm import tqdm

from cryptovote.ballots import CandidateOrderBallot, FirstPreferenceBallot, candidate_elimination_to_candidate_order, \
    candidate_order_to_candidate_elimination, candidate_order_to_first_preference
from cryptovote.damgard_jurik import PrivateKeyShare, PublicKey, threshold_decrypt
from cryptovote.utils import debug, lcm


def eliminate_candidate_set(candidate_set: List[int],
                            ballots: List[CandidateOrderBallot],
                            private_key_shares: List[PrivateKeyShare],
                            public_key: PublicKey) -> List[CandidateOrderBallot]:
    """ Eliminate the given candidate set (1d) """
    debug(f'Eliminating candidates: {candidate_set}')

    # Deal with an empty set of ballots, just in case
    if len(ballots) == 0:
        return []

    # The number of remaining candidates (note that they not necessarily have numbers 1 through num_candidates)
    num_candidates = len(ballots[0].candidates)
    eliminated = [mpz(1) if ballots[0].candidates[i] in candidate_set else mpz(0) for i in range(num_candidates)]
    relevant_columns = set()  # holds non eliminated candidates

    for i in range(num_candidates):
        if eliminated[i] == 0:
            relevant_columns.add(i)

    result = []

    for ballot in ballots:
        ceb = candidate_order_to_candidate_elimination(ballot, eliminated, private_key_shares, public_key)
        prefix_sum = public_key.encrypt(0)

        for i in range(num_candidates):
            prefix_sum += ceb.eliminated[i]
            ceb.preferences[i] -= prefix_sum

        cob = candidate_elimination_to_candidate_order(ceb, private_key_shares)
        updated_candidates = [cob.candidates[i] for i in relevant_columns]
        updated_preferences = [cob.preferences[i] for i in relevant_columns]
        result.append(CandidateOrderBallot(updated_candidates, updated_preferences, cob.weight))

    return result


def compute_first_preference_tallies(ballots: List[CandidateOrderBallot],
                                     private_key_shares: List[PrivateKeyShare],
                                     public_key: PublicKey) -> Tuple[List[FirstPreferenceBallot], List[int]]:
    """ Compute First-Preference Tallies (1b)
        Assumes there is at least one ballot.   """
    debug('Converting CandidateOrderBallots to FirstPreferenceBallots')

    # Initialization
    if len(ballots) == 0:
        raise ValueError

    num_candidates = len(ballots[0].candidates)
    encrypted_tallies = [public_key.encrypt(0) for _ in range(num_candidates)]

    # Perform computation
    fpb_ballots = []

    for ballot in tqdm(ballots, total=len(ballots)):
        fpb = candidate_order_to_first_preference(ballot, private_key_shares, public_key)
        fpb_ballots.append(fpb)

        for i in range(num_candidates):
            encrypted_tallies[i] += fpb.weights[i]

    # Return the result
    debug('Decrypting tallies')
    decrypted_tallies = [threshold_decrypt(encrypted_tally, private_key_shares)
                         for encrypted_tally in tqdm(encrypted_tallies, total=len(encrypted_tallies))]

    return fpb_ballots, decrypted_tallies


def reweight_votes(ballots: List[FirstPreferenceBallot],
                   elected: List[int],
                   quota: int,
                   tallies: List[int],
                   public_key: PublicKey) -> Tuple[List[CandidateOrderBallot], int]:
    """ Reweight the votes for elected candidates in S with quota. """
    debug('Reweighting votes')

    if len(ballots) == 0:
        raise ValueError

    candidates = ballots[0].candidates
    num_candidates = len(candidates)
    d_lcm = mpz(1)

    for i in range(num_candidates):
        # only consider the elected candidates
        if candidates[i] in elected:
            # TODO: do we want to do the approximation from the paper?
            d_lcm = lcm(d_lcm, tallies[i])

    result = []

    for ballot in ballots:
        new_weight = public_key.encrypt(0)

        for i in range(num_candidates):
            ballot.weights[i] *= d_lcm

            if candidates[i] in elected:
                ballot.weights[i] *= tallies[i] - quota
                ballot.weights[i] /= tallies[i]

            new_weight += ballot.weights[i]

        result.append(CandidateOrderBallot(ballot.candidates, ballot.preferences, new_weight))

    return result, d_lcm


def stv_tally(ballots: List[CandidateOrderBallot],
              seats: int,
              stop_candidate: int,
              private_key_shares: List[PrivateKeyShare],
              public_key: PublicKey) -> List[int]:
    """ The main protocol of the ShuffleSum voting algorithm.
        Assumes there is at least one ballot.
        Returns a list of elected candidates. """
    if len(ballots) == 0:
        raise ValueError

    c_rem = ballots[0].candidates       # the remaining candidates
    quota = mpz(len(ballots)) // (seats + 1) + 1     # the (droop) quota required for election
    result = []
    offset = mpz(1) if stop_candidate in c_rem else mpz(0)
    round = 0

    while len(c_rem) - offset > seats:
        debug(f'Round {round}')

        fpb_ballots, tallies = compute_first_preference_tallies(ballots, private_key_shares, public_key)
        elected = []

        for i in range(len(c_rem)):
            if c_rem[i] == stop_candidate:
                continue
            if tallies[i] >= quota:
                elected.append(c_rem[i])

        debug(f'{len(elected)} candidates elected')

        if len(elected) > 0:
            debug(f'Elected candidates: {elected}')

            result += elected
            seats -= len(elected)
            ballots, d_lcm = reweight_votes(fpb_ballots, elected, quota, tallies, public_key)
            quota *= d_lcm
            ballots = eliminate_candidate_set(elected, ballots, private_key_shares, public_key)
        else:
            i = None

            for j in range(len(c_rem)):
                if c_rem[j] == stop_candidate:
                    continue

                if i is None or tallies[j] < tallies[i]:
                    i = j

            debug(f'Candidate with fewest votes = {c_rem[i]}')

            ballots = eliminate_candidate_set([c_rem[i]], ballots, private_key_shares, public_key)

        c_rem = ballots[0].candidates

    for i in range(len(c_rem)):
        if c_rem[i] != stop_candidate:
            result.append(c_rem[i])

    return result
