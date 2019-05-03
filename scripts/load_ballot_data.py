from argparse import ArgumentParser
from collections import defaultdict


def load_ballot_data(master_lookup_path: str, ballot_image_path: str):
    # Load candidates from master lookup
    candidate_id_to_candidate_name = {}
    candidate_id_to_contest_id = {}
    contest_id_to_contest_name = {}

    with open(master_lookup_path) as f:
        for line in f:
            if line.startswith('Candidate'):
                candidate_id = int(line[10:17])
                candidate_name = line[17:67].strip()
                contest_id = int(line[74:81])

                candidate_id_to_candidate_name[candidate_id] = candidate_name
                candidate_id_to_contest_id[candidate_id] = contest_id

            elif line.startswith('Contest'):
                contest_id = int(line[10:17])
                contest_name = line[17:67].strip()

                contest_id_to_contest_name[contest_id] = contest_name

    # Map each contest_id to a set of all candidate_ids in the contest
    contest_id_to_candidate_ids = defaultdict(set)
    for candidate_id, contest_id in candidate_id_to_contest_id.items():
        contest_id_to_candidate_ids[contest_id].add(candidate_id)

    # Assert no candidate in multiple contests
    assert len(set.intersection(*contest_id_to_candidate_ids.values())) == 0

    # Load ballots
    voter_id_to_votes = defaultdict(list)

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

    # Assert that all voters voted for the same number of candidates
    assert len({len(votes) for votes in voter_id_to_votes.values()}) == 1

    # Prune bad votes (i.e. if there is a vote with candidate_id == 0)
    for voter_id, votes in list(voter_id_to_votes.items()):
        if any(vote['candidate_id'] == 0 for vote in votes):
            voter_id_to_votes.pop(voter_id)

    # Convert votes to an ordered list of candidate_ids
    for voter_id, votes in voter_id_to_votes.items():
        voter_id_to_votes[voter_id] = [vote['candidate_id'] for vote in sorted(votes, key=lambda vote: vote['candidate_rank'])]

    print(f'Number of valid votes = {len(voter_id_to_votes):,}')

    # Convert to CandidateOrderBallots
    contest_id_to_ballots = {}
    for


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