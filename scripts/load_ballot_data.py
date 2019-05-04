from argparse import ArgumentParser
from collections import defaultdict

from cryptovote.ballots import CandidateOrderBallot
from cryptovote.damgard_jurik import keygen, PublicKey


STOP_CANDIDATE_NAME = 'STOP'


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

    print(f'Number of valid votes = {sum(len(votes) for votes in voter_id_to_votes.values()):,}')
    print(f'Number of invalid votes = {num_invalid_votes:,}')

    # Assert that each vote does not reuse a rank for multiple candidates
    assert all(len(set(candidate_ranks)) == len(candidate_ranks)
               for votes in voter_id_to_votes.values()
               for candidate_ranks in votes.values())

    # Adjust candidate ranks to be in contiguous order from 1 to n
    for votes in voter_id_to_votes.values():
        old_candidate_ranks = votes.values()
        old_rank_to_new_rank = {old_rank: index + 1 for index, old_rank in enumerate(old_candidate_ranks)}

        for candidate_id, candidate_rank in votes.items():
            votes[candidate_id] = old_rank_to_new_rank[candidate_rank]
    
    # Assert that vote ranks are unique and are in a contiguous range from 1 to n
    for voter_id, votes in list(voter_id_to_votes.items()):
        candidate_ranks = list(votes.values())

        # Assert that vote ranks are unique
        assert len(set(candidate_ranks)) == len(candidate_ranks)

        # Assert that vote ranks are in a contiguous range from 1 to n
        if not (candidate_ranks == list(range(1, max(candidate_ranks) + 1))):
            import pdb; pdb.set_trace()
        assert candidate_ranks == list(range(1, max(candidate_ranks) + 1))

    # Assert that each voter only voted in one contest
    assert set.intersection(*contest_id_to_voter_ids.values()) == set()

    # For each contest, convert votes to CandidateOrderBallots
    contest_id_to_contest = {}
    for contest_id, voter_ids in contest_id_to_voter_ids.items():
        # Determine candidates in contest and sort
        candidate_ids = sorted(contest_id_to_candidate_ids[contest_id])

        # Determine stop candidate id for this contest
        stop_candidate_id = max(candidate_ids) + 1

        # Initialize ballots list for this contest
        ballots = []

        # Create CandidateOrderBallots from votes
        for voter_id in voter_ids:
            # Get votes for voter
            votes = voter_id_to_votes[voter_id]

            # Determine preferences
            preferences = [votes[candidate_id] for candidate_id in candidate_ids]

            # Encrypt
            preferences = [public_key.encrypt(preference) for preference in preferences]
            weight = public_key.encrypt(1)

            # Create ballot
            ballot = CandidateOrderBallot(candidate_ids, preferences, weight)
            ballots.append(ballot)

        # Create contest
        contest_id_to_contest[contest_id] = {
            'ballots': ballots,
            'candidate_id_to_candidate_name': {
                **{candidate_id: candidate_id_to_candidate_name[candidate_id]
                   for candidate_id in candidate_ids
                   },
                **{stop_candidate_id: STOP_CANDIDATE_NAME}
            },
            'stop_candidate_id': stop_candidate_id
        }

    import pdb; pdb.set_trace()

    return contest_id_to_contest


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--master_lookup_path', type=str, required=True,
                        help='Path to a .txt file containing a master lookup')
    parser.add_argument('--ballot_image_path', type=str, required=True,
                        help='Path to a .txt file containing a ballot image')
    args = parser.parse_args()

    public_key, private_key_shares = keygen(n_bits=32, s=3, threshold=4, n_shares=10)

    load_ballot_data(
        master_lookup_path=args.master_lookup_path,
        ballot_image_path=args.ballot_image_path,
        public_key=public_key
    )
