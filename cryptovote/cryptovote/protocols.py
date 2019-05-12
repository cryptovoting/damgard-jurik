#!/usr/bin/env python3
"""
protocols.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains main protocols for the ShuffleSum voting algorithm.

"""
from functools import partial
from multiprocessing import Pool
from typing import List, Set, Tuple

from gmpy2 import mpz
from tqdm import tqdm

from cryptovote.ballots import CandidateEliminationBallot, CandidateOrderBallot, FirstPreferenceBallot,\
    candidate_elimination_to_candidate_order, candidate_order_to_candidate_elimination,\
    candidate_order_to_first_preference
from cryptovote.damgard_jurik import EncryptedNumber, PrivateKeyRing, PublicKey
from cryptovote.utils import debug, lcm


def compute_first_preference_tallies(cob_ballots: List[CandidateOrderBallot],
                                     private_key_ring: PrivateKeyRing,
                                     public_key: PublicKey) -> Tuple[List[FirstPreferenceBallot], List[int]]:
    """ Compute First-Preference Tallies (1b)
        Assumes there is at least one ballot.   """
    debug('Computing first preference tallies')

    # Initialization
    if len(cob_ballots) == 0:
        raise ValueError('Need non-zero number of ballots')

    num_candidates = len(cob_ballots[0].candidates)

    cob_to_fpb = partial(
        candidate_order_to_first_preference,
        private_key_ring=private_key_ring,
        public_key=public_key
    )

    debug('Converting CandidateOrderBallots to FirstPreferenceBallots')
    with Pool() as pool:
        fpb_ballots = list(tqdm(pool.imap(cob_to_fpb, cob_ballots), total=len(cob_ballots)))

    debug('Summing encrypted weights')
    zero = public_key.encrypt(0)
    encrypted_tallies = [sum((fpb.weights[i] for fpb in fpb_ballots), zero) for i in range(num_candidates)]

    debug('Decrypting tallies')
    decrypted_tallies = private_key_ring.decrypt_list(encrypted_tallies)

    return fpb_ballots, decrypted_tallies


def reweight_and_convert_ballot(fpb: FirstPreferenceBallot,
                               d_lcm: int,
                               elected: Set[int],
                               tallies: List[int],
                               quota: int,
                               zero: EncryptedNumber) -> CandidateOrderBallot:
    """ Reweight a single FirstPreferenceBallot and convert it to a CandidateOrderBallot."""
    new_weight = zero

    for i in range(len(fpb.candidates)):
        fpb.weights[i] *= d_lcm

        if fpb.candidates[i] in elected:
            fpb.weights[i] *= tallies[i] - quota
            fpb.weights[i] /= tallies[i]

        new_weight += fpb.weights[i]

    return CandidateOrderBallot(fpb.candidates, fpb.preferences, new_weight)


def reweight_votes(fpb_ballots: List[FirstPreferenceBallot],
                   elected: Set[int],
                   quota: int,
                   tallies: List[int],
                   public_key: PublicKey) -> Tuple[List[CandidateOrderBallot], int]:
    """ Reweight the votes for elected candidates in S with quota. """
    debug('Reweighting votes')

    if len(fpb_ballots) == 0:
        raise ValueError('Need non-zero number of ballots')

    candidates = fpb_ballots[0].candidates
    num_candidates = len(candidates)
    d_lcm = lcm(*[tallies[i] for i in range(num_candidates) if candidates[i] in elected])

    debug('Reweighting and converting FirstPreferenceBallots to CandidateOrderBallots')
    reweight_and_fbp_to_cob = partial(
        reweight_and_convert_ballot,
        d_lcm=d_lcm,
        elected=elected,
        tallies=tallies,
        quota=quota,
        zero=public_key.encrypt(0)
    )

    # Note: this is slower in parallel than sequentially so don't parallelize
    cob_ballots = list(tqdm(map(reweight_and_fbp_to_cob, fpb_ballots), total=len(fpb_ballots)))

    return cob_ballots, d_lcm


def update_preferences(ceb: CandidateEliminationBallot, zero: EncryptedNumber) -> CandidateEliminationBallot:
    """ Updates the preferences of a ballot based on the eliminated candidates."""
    prefix_sum = zero

    for i in range(len(ceb.candidates)):
        prefix_sum += ceb.eliminated[i]
        ceb.preferences[i] -= prefix_sum

    return ceb


def remove_candidates(cob: CandidateOrderBallot, remaining_candidate_indices: Set[int]) -> CandidateOrderBallot:
    """ Removes any candidates not present in remaining_candidate_indices from a ballot."""
    cob.candidates = [cob.candidates[i] for i in remaining_candidate_indices]
    cob.preferences = [cob.preferences[i] for i in remaining_candidate_indices]

    return cob


def eliminate_candidate_set(candidate_set: Set[int],
                            cob_ballots: List[CandidateOrderBallot],
                            private_key_ring: PrivateKeyRing,
                            public_key: PublicKey) -> List[CandidateOrderBallot]:
    """ Eliminate the given candidate set (1d) """
    debug(f'Eliminating candidates: {candidate_set}')

    # Deal with an empty set of ballots, just in case
    if len(cob_ballots) == 0:
        return []

    # The number of remaining candidates (note that they not necessarily have numbers 1 through num_candidates)
    num_candidates = len(cob_ballots[0].candidates)
    eliminated = [mpz(1) if candidate in candidate_set else mpz(0) for candidate in cob_ballots[0].candidates]
    remaining_candidate_indices = {i for i in range(num_candidates) if eliminated[i] == 0}

    cob_to_ceb = partial(
        candidate_order_to_candidate_elimination,
        eliminated=eliminated,
        private_key_ring=private_key_ring,
        public_key=public_key
    )
    update_preferences_fn = partial(
        update_preferences,
        zero=public_key.encrypt(0)
    )
    ceb_to_cob = partial(
        candidate_elimination_to_candidate_order,
        private_key_ring=private_key_ring
    )
    remove_candidates_fn = partial(
        remove_candidates,
        remaining_candidate_indices=remaining_candidate_indices
    )

    with Pool() as pool:
        debug('Converting CandidateOrderBallots to CandidateEliminationBallots')
        ceb_ballots = list(tqdm(pool.imap(cob_to_ceb, cob_ballots), total=len(cob_ballots)))

        debug('Updating preferences based on eliminated candidates')
        ceb_ballots = list(tqdm(pool.imap(update_preferences_fn, ceb_ballots), total=len(ceb_ballots)))

        debug('Converting CandidateEliminationBallots to CandidateOrderBallots')
        cob_ballots = list(tqdm(pool.imap(ceb_to_cob, ceb_ballots), total=len(ceb_ballots)))

    # Note: this is slower in parallel than sequentially so don't parallelize
    debug('Removing candidates and preferences for candidates that have been eliminated')
    cob_ballots = list(tqdm(map(remove_candidates_fn, cob_ballots), total=len(cob_ballots)))

    return cob_ballots


def stv_tally(cob_ballots: List[CandidateOrderBallot],
              seats: int,
              stop_candidate: int,
              private_key_ring: PrivateKeyRing,
              public_key: PublicKey) -> List[int]:
    """ The main protocol of the ShuffleSum voting algorithm.
        Assumes there is at least one ballot.
        Returns a list of elected candidates. """
    if len(cob_ballots) == 0:
        raise ValueError('Need non-zero number of ballots')

    c_rem = cob_ballots[0].candidates       # the remaining candidates
    quota = mpz(len(cob_ballots)) // (seats + 1) + 1     # the (droop) quota required for election
    result = []
    offset = 1 if stop_candidate in c_rem else 0
    round = 0

    while len(c_rem) - offset > seats:
        debug(f'Round {round}')

        fpb_ballots, tallies = compute_first_preference_tallies(cob_ballots, private_key_ring, public_key)
        elected = set()

        # TODO: print tallies

        for i in range(len(c_rem)):
            if c_rem[i] == stop_candidate:
                continue

            if tallies[i] >= quota:
                elected.add(c_rem[i])

        debug(f'{len(elected)} candidates elected')

        if len(elected) > 0:
            debug(f'Elected candidates: {elected}')

            result += elected
            seats -= len(elected)
            cob_ballots, d_lcm = reweight_votes(fpb_ballots, elected, quota, tallies, public_key)
            quota *= d_lcm
            cob_ballots = eliminate_candidate_set(elected, cob_ballots, private_key_ring, public_key)
        else:
            i = None

            for j in range(len(c_rem)):
                if c_rem[j] == stop_candidate:
                    continue

                if i is None or tallies[j] < tallies[i]:
                    i = j

            debug(f'Candidate with fewest votes = {c_rem[i]}')

            cob_ballots = eliminate_candidate_set({c_rem[i]}, cob_ballots, private_key_ring, public_key)

        c_rem = cob_ballots[0].candidates

        debug(f'Remaining candidates: {c_rem}')

        round += 1

    for i in range(len(c_rem)):
        if c_rem[i] != stop_candidate:
            result.append(c_rem[i])

    return result
