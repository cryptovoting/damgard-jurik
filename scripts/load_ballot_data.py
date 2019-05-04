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
from cryptovote.damgard_jurik import keygen, PublicKey


def load_ballot_data(master_lookup_path: str,
                     ballot_image_path: str,
                     public_key: PublicKey) -> dict:
    # Load candidates from master lookup
    contest_id_to_candidate_ids = defaultdict(set)
    candidate_id_to_candidate_name = {}
    contest_id_to_contest_name = {}

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


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--master_lookup', type=str, required=True,
                        help='Path to a .txt file containing a master lookup')
    parser.add_argument('--ballot_image', type=str, required=True,
                        help='Path to a .txt file containing a ballot image')
    args = parser.parse_args()

    public_key, private_key_shares = keygen(n_bits=32, s=3, threshold=4, n_shares=10)

    load_ballot_data(
        master_lookup_path=args.master_lookup_path,
        ballot_image_path=args.ballot_image_path,
        public_key=public_key
    )
