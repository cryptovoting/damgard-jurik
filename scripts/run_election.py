from argparse import ArgumentParser
import time

from cryptovote.damgard_jurik import keygen
from cryptovote.protocols import stv_tally

from scripts.load_ballot_data import load_ballot_data


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--master_lookup', type=str, required=True,
                        help='Path to a .txt file containing a master lookup.')
    parser.add_argument('--ballot_image', type=str, required=True,
                        help='Path to a .txt file containing a ballot image.')
    parser.add_argument('--seats', type=int, default=1,
                        help='The number of candidates that need to be elected.')
    parser.add_argument('--n_bits', type=int, default=64,
                        help='The number of bits to use in the public and private keys.')
    parser.add_argument('--s', type=int, default=1,
                        help='The power to which n = p * q will be raised. Plaintexts live in Z_n^s.')
    parser.add_argument('--threshold', type=int, default=3,
                        help='The minimum number of PrivateKeyShares needed to decrypt an encrypted number.')
    parser.add_argument('--n_shares', type=int, default=3,
                        help='The number of PrivateKeyShares to generate.')
    args = parser.parse_args()

    public_key, private_key_ring = keygen(
        n_bits=args.n_bits,
        s=args.s,
        threshold=args.threshold,
        n_shares=args.n_shares
    )
    
    contest_id_to_contest = load_ballot_data(
        master_lookup_path=args.master_lookup,
        ballot_image_path=args.ballot_image,
        public_key=public_key
    )

    for contest_id, contest in contest_id_to_contest.items():
        print(f'Processing contest id = {contest_id}')

        num_candidates = len(contest['candidate_id_to_candidate_name'])
        print(f'Number of candidates = {num_candidates}')
        print(f'Number of voters = {len(contest["ballots"]):,}')

        start = time.time()
        result = stv_tally(
            cob_ballots=contest['ballots'],
            seats=args.seats,
            stop_candidate=contest['stop_candidate_id'],
            private_key_ring=private_key_ring,
            public_key=public_key
        )
        print(f'Time = {time.time() - start}')

        print('Elected candidates')
        for elected in result:
            print(contest['candidate_id_to_candidate_name'][elected])
