#!/usr/bin/env python3
"""
load_ballot_data.py
Boucher, Govedič, Saowakon, Swanson 2019

A script which loads a ballot image and corresponding master lookup,
performs validation of the votes and prunes invalid votes,
and encrypts the votes and converts them to CandidateOrderBallots
for use with Shuffle Sum STV vote tallying.
"""
from argparse import ArgumentParser
from collections import defaultdict

from tqdm import tqdm

from cryptovote.ballots import CandidateOrderBallot
#from cryptovote.damgard_jurik import keygen, PublicKey
from cryptovote.crypto import keygen, PublicKey

from cryptovote.crypto import PrivateKey

from cryptovote.protocols import stv_tally

from typing import List


def load_ballot_data(master_lookup_path: str,
                     ballot_image_path: str,
                     public_key: PublicKey) -> dict:
    # Load candidates from master lookup
    contest_id_to_candidate_ids = defaultdict(set)
    candidate_id_to_candidate_name = {}
    contest_id_to_contest_name = {}

    print("looking at", master_lookup_path)

    with open(master_lookup_path) as f:
        for line in f:
            if line.startswith('Candidate'):
                candidate_id = int(line[10:17])
                candidate_name = line[17:67].strip()
                contest_id = int(line[74:81])

                contest_id_to_candidate_ids[contest_id].add(candidate_id)
                candidate_id_to_candidate_name[candidate_id] = candidate_name

            elif line.startswith('Contest'):
                contest_id = int(line[10:17])
                contest_name = line[17:67].strip()

                contest_id_to_contest_name[contest_id] = contest_name

    # Assert no candidate in multiple contests
    assert set.intersection(*contest_id_to_candidate_ids.values()) == set()

    # Choose stop candidate id and name
    candidate_ids = set(candidate_id_to_candidate_name.keys())
    stop_candidate_id = max(candidate_ids) + 1
    candidate_id_to_candidate_name[stop_candidate_id] = 'STOP'

    # Load votes
    voter_id_to_votes = defaultdict(dict)
    contest_id_to_voter_ids = defaultdict(set)
    num_invalid_votes = 0

    with open(ballot_image_path) as f:
        for line in f:
            contest_id = int(line[0:7])
            voter_id = int(line[7:16])
            candidate_id = int(line[36:43])
            candidate_rank = int(line[33:36])

            # Skip vote for a candidate not in the candidate set
            if candidate_id not in candidate_id_to_candidate_name:
                num_invalid_votes += 1
                continue

            # Get votes for voter_id
            votes = voter_id_to_votes[voter_id]

            # Add vote
            # Note: if voter is voting for the same candidate twice, take the minimum rank
            votes[candidate_id] = min(candidate_rank, votes.get(candidate_id, float('inf')))
            contest_id_to_voter_ids[contest_id].add(voter_id)

    print(f'Number of invalid votes = {num_invalid_votes:,}')
    print(f'Number of valid votes = {sum(len(votes) for votes in voter_id_to_votes.values()):,}')
    print(f'Number of voters = {len(voter_id_to_votes):,}')

    # Assert that each vote does not reuse a rank for multiple candidates
    for votes in voter_id_to_votes.values():
        candidate_ranks = votes.values()

        assert len(set(candidate_ranks)) == len(candidate_ranks)

    # Adjust candidate ranks to be in contiguous order from 1 to n
    for votes in voter_id_to_votes.values():
        old_candidate_ranks = votes.values()
        old_rank_to_new_rank = {old_rank: index + 1 for index, old_rank in enumerate(old_candidate_ranks)}

        for candidate_id, candidate_rank in votes.items():
            votes[candidate_id] = old_rank_to_new_rank[candidate_rank]

        # Assert that we did the mapping correctly
        candidate_ranks = list(votes.values())

        assert candidate_ranks == list(range(1, max(candidate_ranks) + 1))

    # Assert that each voter only voted in one contest
    assert set.intersection(*contest_id_to_voter_ids.values()) == set()

    # For each contest, convert votes to CandidateOrderBallots
    contest_id_to_contest = {}
    for contest_id, voter_ids in tqdm(contest_id_to_voter_ids.items(), total=len(contest_id_to_voter_ids)):
        # Determine candidates in contest and sort
        candidate_ids = sorted(contest_id_to_candidate_ids[contest_id]) + [stop_candidate_id]
        num_candidates = len(candidate_ids)

        # Create CandidateOrderBallots from votes
        ballots = []

        for voter_id in tqdm(voter_ids, total=len(voter_ids)):
            # Get votes for voter
            votes = voter_id_to_votes[voter_id]

            # Get stop candidate preference
            stop_candidate_rank = len(votes) + 1

            # Determine remaining ranks for candidates not voted for
            remaining_ranks = set(range(stop_candidate_rank + 1, num_candidates + 1))

            # Determine preferences, selecting random preference for candidates not voted form
            preferences = []
            for candidate_id in candidate_ids:
                if candidate_id in votes:
                    candidate_rank = votes[candidate_id]
                    preferences.append(candidate_rank)

                elif candidate_id == stop_candidate_id:
                    preferences.append(stop_candidate_rank)

                else:
                    # TODO: need more secure source of randomness than set pop
                    preferences.append(remaining_ranks.pop())

            # Encrypt preferences and weight
            preferences = [public_key.encrypt(preference) for preference in preferences]
            weight = public_key.encrypt(1)

            # Create ballot
            ballot = CandidateOrderBallot(candidate_ids, preferences, weight)
            ballots.append(ballot)

        # Create contest
        contest_id_to_contest[contest_id] = {
            'ballots': ballots,
            'candidate_id_to_candidate_name': {
                candidate_id: candidate_id_to_candidate_name[candidate_id]
                for candidate_id in candidate_ids
            },
            'stop_candidate_id': stop_candidate_id
        }

    return contest_id_to_contest

def fake_tally(ballots: List[CandidateOrderBallot], seats: int, stop_candidate: int, private_key: PrivateKey, public_key: PublicKey) -> List[int]:
    """ The main protocol of the ShuffleSum voting algorithm.
        Assumes there is at least one ballot.
        Returns a list of elected candidates. """
    if len(ballots) == 0:
        raise ValueError
    c_rem = ballots[0].candidates[:]    # the remaining candidates
    q = len(ballots)//(seats+1) + 1     # the quota required for election
    result = []
    offset = 1 if stop_candidate in c_rem else 0
    decrypted_ballots = []
    for ballot in ballots:
        decrypted_ballots.append([ballot.candidates, [private_key.decrypt(preference) for preference in ballot.preferences], private_key.decrypt(ballot.weight)])
    while len(c_rem)-offset > seats:
        print("Computing FPT...")
        t = [0 for i in range(len(c_rem))]
        for ballot in decrypted_ballots:
            vote_for = 0
            for i in range(len(c_rem)):
                if ballot[1][i] < ballot[1][vote_for]:
                    vote_for = i
            t[vote_for] += ballot[2]
        elected = []
        for i in range(len(c_rem)):
            if c_rem[i] == stop_candidate:
                continue
            if t[i] >= q:               # TODO NOTE: Not sure if it needs to be >= or >
                elected.append(c_rem[i])
        if len(elected) > 0:
            result += elected
            seats -= len(elected)
            print(len(elected), "candidates elected. Reweighting votes...")
            print("Elected ", elected)
            for ballot in decrypted_ballots:
                vote_for = 0
                for i in range(len(c_rem)):
                    if ballot[1][i] < ballot[1][vote_for]:
                        vote_for = i
                if c_rem[vote_for] in elected:
                    ballot[2] = ballot[2]*(t[vote_for]-q)/t[vote_for]
            print("Eliminating set...")
            to_eliminate = elected
            for i in range(len(decrypted_ballots)):
                new_candidates = []
                new_preferences = []
                for j in range(len(decrypted_ballots[i][0])):
                    if decrypted_ballots[i][0][j] not in to_eliminate:
                        new_candidates.append(decrypted_ballots[i][0][j])
                        new_preferences.append(decrypted_ballots[i][1][j])
                decrypted_ballots[i] = [new_candidates, new_preferences, decrypted_ballots[i][2]]
        else:
            print("Eliminating from total of ", len(c_rem))
            print("I.e., ", c_rem)
            i = None
            for j in range(len(c_rem)):
                if c_rem[j] == stop_candidate:
                    continue
                if i == None or t[j] < t[i]:
                    i = j
            print("Eliminating set...", i, c_rem[i])
            to_eliminate = [c_rem[i]]
            for i in range(len(decrypted_ballots)):
                new_candidates = []
                new_preferences = []
                for j in range(len(decrypted_ballots[i][0])):
                    if decrypted_ballots[i][0][j] not in to_eliminate:
                        new_candidates.append(decrypted_ballots[i][0][j])
                        new_preferences.append(decrypted_ballots[i][1][j])
                decrypted_ballots[i] = [new_candidates, new_preferences, decrypted_ballots[i][2]]
        c_rem = decrypted_ballots[0][0][:]
    for i in range(len(c_rem)):
        if c_rem[i] != stop_candidate:
            result.append(c_rem[i])
    return result


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--master_lookup', type=str, required=True,
                        help='Path to a .txt file containing a master lookup')
    parser.add_argument('--ballot_image', type=str, required=True,
                        help='Path to a .txt file containing a ballot image')
    args = parser.parse_args()

    #public_key, private_key_shares = keygen(n_bits=32, s=3, threshold=4, n_shares=10)
    public_key, private_key = keygen(n_bits=256)

    contest_id_to_contest = load_ballot_data(
        master_lookup_path=args.master_lookup,
        ballot_image_path=args.ballot_image,
        public_key=public_key
    )

    # Uncomment the following to simulate the election straightforwardly

    """
    for contest_id in contest_id_to_contest:
        print("Processing ", contest_id)
        contest = contest_id_to_contest[contest_id]
        C = len(contest['candidate_id_to_candidate_name'])
        print("C:", C)
        result = fake_tally(contest['ballots'], C//2, contest['stop_candidate_id'], private_key, public_key)
        print(result)
        for elected in result:
            print(contest['candidate_id_to_candidate_name'][elected])
    """

    # Uncomment the following to simulate the election with ShuffleSum

    """
    for contest_id in contest_id_to_contest:
        print("Processing ", contest_id)
        contest = contest_id_to_contest[contest_id]
        C = len(contest['candidate_id_to_candidate_name'])
        print("C:", C)
        result = stv_tally(contest['ballots'], C//2, contest['stop_candidate_id'], private_key, public_key)
        print(result)
        for elected in result:
            print(contest['candidate_id_to_candidate_name'][elected])
    """