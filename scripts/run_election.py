from argparse import ArgumentParser

from cryptovote.damgard_jurik import keygen
from cryptovote.protocols import stv_tally

from scripts.load_ballot_data import load_ballot_data


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--master_lookup', type=str, required=True,
                        help='Path to a .txt file containing a master lookup')
    parser.add_argument('--ballot_image', type=str, required=True,
                        help='Path to a .txt file containing a ballot image')
    args = parser.parse_args()

    public_key, private_key_shares = keygen(n_bits=32, s=1, threshold=1, n_shares=1)

    contest_id_to_contest = load_ballot_data(
        master_lookup_path=args.master_lookup,
        ballot_image_path=args.ballot_image,
        public_key=public_key
    )

    import time

    for contest_id, contest in contest_id_to_contest.items():
        start = time.time()
        print(f'Processing contest id = {contest_id}')

        num_candidates = len(contest['candidate_id_to_candidate_name'])
        print(f'Number of candidates = {num_candidates}')

        result = stv_tally(
            ballots=contest['ballots'],
            seats=1,
            stop_candidate=contest['stop_candidate_id'],
            private_key_shares=private_key_shares,
            public_key=public_key
        )

        print('Result')
        print(result)

        print('Elected candidates')
        for elected in result:
            print(contest['candidate_id_to_candidate_name'][elected])

        print(f'Time = {time.time() - start}')
        print()
