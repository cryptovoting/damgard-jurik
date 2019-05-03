from argparse import ArgumentParser
from collections import defaultdict


def load_ballot_data(master_lookup_path: str, ballot_image_path: str):
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
    assert len(set.intersection(*contest_id_to_candidate_ids.values())) == 0

    # Determine fixed order for candidates in each contest
    contest_id_to_candidate_ids = {contest_id: sorted(candidate_ids) for contest_id, candidate_ids in contest_id_to_candidate_ids.items()}

    # Load ballots
    voter_id_to_votes = defaultdict(list)
    contest_id_to_voter_ids = defaultdict(set)

    with open(ballot_image_path) as f:
        for line in f:
            contest_id = int(line[0:7])
            voter_id = int(line[7:16])
            candidate_id = int(line[36:43])
            candidate_rank = int(line[33:36])

            voter_id_to_votes[voter_id].append({
                'contest_id': contest_id,
                'candidate_id': candidate_id,
                'candidate_rank': candidate_rank
            })
            contest_id_to_voter_ids[contest_id].add(voter_id)

    # Prune invalid votes (i.e. if there is a vote with candidate_id == 0)
    for voter_id, votes in list(voter_id_to_votes.items()):
        if any(vote['candidate_id'] == 0 for vote in votes):
            voter_id_to_votes.pop(voter_id)

    # Assert that all voters voted for the same number of candidates
    assert len({len(votes) for votes in voter_id_to_votes.values()}) == 1

    # Assert that each voter only voted in one contest
    assert all(len({vote['contest_id'] for vote in votes}) == 1 for votes in voter_id_to_votes.values())

    # For each contest, convert votes to CandidateOrderBallots
    # TODO: encryption
    contest_id_to_ballots = {}
    for contest_id, voter_ids in contest_id_to_voter_ids.items():
        candidates = contest_id_to_candidate_ids[contest_id]
        ballots = []

        for voter_id in voter_ids:
            votes = voter_id_to_votes[voter_id]
            preferences = []
            # TODO: create candidate order ballot


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--master_lookup_path', type=str, required=True,
                        help='Path to a .txt file containing a master lookup')
    parser.add_argument('--ballot_image_path', type=str, required=True,
                        help='Path to a .txt file containing a ballot image')
    args = parser.parse_args()

    load_ballot_data(
        master_lookup_path=args.master_lookup_path,
        ballot_image_path=args.ballot_image_path
    )
m