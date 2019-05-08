from argparse import ArgumentParser
from typing import List

from gmpy2 import mpz

from cryptovote.ballots import CandidateOrderBallot
from cryptovote.damgard_jurik import keygen, PrivateKeyShare, threshold_decrypt

from scripts.load_ballot_data import load_ballot_data


def fake_tally(ballots: List[CandidateOrderBallot],
               seats: int,
               stop_candidate: int,
               private_key_shares: List[PrivateKeyShare]) -> List[int]:
    """ The main protocol of the ShuffleSum voting algorithm.
        Assumes there is at least one ballot.
        Returns a list of elected candidates. """
    if len(ballots) == 0:
        raise ValueError

    c_rem = ballots[0].candidates[:]    # the remaining candidates
    quota = mpz(len(ballots)) // (seats + 1) + 1     # the quota required for election
    result = []
    offset = mpz(1) if stop_candidate in c_rem else mpz(0)
    decrypted_ballots = []

    for ballot in ballots:
        decrypted_ballots.append([
            ballot.candidates,
            [threshold_decrypt(preference, private_key_shares) for preference in ballot.preferences],
            threshold_decrypt(ballot.weight, private_key_shares)
        ])

    while len(c_rem)-offset > seats:
        print("Computing FPT...")
        tallies = [mpz(0) for _ in range(len(c_rem))]

        for ballot in decrypted_ballots:
            vote_for = 0

            for i in range(len(c_rem)):
                if ballot[1][i] < ballot[1][vote_for]:
                    vote_for = i

            tallies[vote_for] += ballot[2]

        elected = []

        for i in range(len(c_rem)):
            if c_rem[i] == stop_candidate:
                continue
            if tallies[i] >= quota:               # TODO NOTE: Not sure if it needs to be >= or >
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
                    ballot[2] = ballot[2] * (tallies[vote_for] - quota) / tallies[vote_for]

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
                if i is None or tallies[j] < tallies[i]:
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

        result = fake_tally(
            ballots=contest['ballots'],
            seats=1,
            stop_candidate=contest['stop_candidate_id'],
            private_key_shares=private_key_shares
        )

        print('Result')
        print(result)
        print()

        print('Elected candidates')
        for elected in result:
            print(contest['candidate_id_to_candidate_name'][elected])

        print(f'Time = {time.time() - start}')
        print()
