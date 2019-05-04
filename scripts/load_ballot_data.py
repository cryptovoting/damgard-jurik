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

    with open(ballot_image_path) as f:
        for line in f:
            contest_id = int(line[0:7])
            voter_id = int(line[7:16])
            candidate_id = int(line[36:43])
            candidate_rank = int(line[33:36])

            voter_id_to_votes[voter_id][candidate_id] = candidate_rank
            contest_id_to_voter_ids[contest_id].add(voter_id)


    # Assert that each voter doesn't vote multiple times for a candidate
    assert all(len(set(candidate_ranks)) == len(candidate_ranks)
               for votes in voter_id_to_votes.values()
               for candidate_ranks in votes.values())

    # Prune votes that are invalid because either
    # - The vote includes a candidate with candidate_id == 0
    # - The vote ranks are not a contiguous rank
    # Note: Also adjusts votes that are contiguous but don't start at 1 to start at 1
    print(f'Number of voters before pruning = {len(voter_id_to_votes):,}')
    num_candidate_id_0 = num_non_unique_candidates = num_non_contiguous_ranks = 0

    for voter_id, votes in list(voter_id_to_votes.items()):
        candidate_ids, candidate_ranks = zip(*votes.items())
        min_rank, max_rank = min(candidate_ranks), max(candidate_ranks)

        if any(candidate_id == 0 for candidate_id in candidate_ids):
            num_candidate_id_0 += 1
            voter_id_to_votes.pop(voter_id)

        elif len(set(candidate_ranks)) != len(candidate_ranks):
            num_non_unique_candidates += 1
            voter_id_to_votes.pop(voter_id)

        elif candidate_ranks != tuple(range(min_rank, max_rank + 1)):
            num_non_contiguous_ranks += 1
            voter_id_to_votes.pop(voter_id)

        # Fix candidate_ranks if not starting at 1
        for candidate_id, candidate_rank in votes.items():
            votes[candidate_id] = candidate_rank - min_rank + 1

    print(f'Number of voters after pruning = {len(voter_id_to_votes):,}')
    print(f'Number of invalid votes due to candidate_id == 0 = {num_candidate_id_0:,}')
    print(f'Number of invalid votes due to non-unique candidate ranks = {num_non_unique_candidates:,}')
    print(f'Number of invalid votes due to non-contiguous candidate ranks = {num_non_contiguous_ranks:,}')

    # Fix votes that put preferences in non-contiguous order
    for votes in voter_id_to_votes.values():


    exit()

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
