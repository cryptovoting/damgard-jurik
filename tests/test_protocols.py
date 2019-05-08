#!/usr/bin/env python3
"""
test.py
Boucher, Govedič, Saowakon, Swanson 2019

Unit tests for protocols.

"""
from typing import List
import unittest

from cryptovote.ballots import CandidateOrderBallot, FirstPreferenceBallot
from cryptovote.protocols import compute_first_preference_tallies, eliminate_candidate_set, reweight_votes
from cryptovote.damgard_jurik import EncryptedNumber, keygen, PrivateKeyShare, PublicKey, threshold_decrypt


def decrypt_list(l: List[EncryptedNumber], private_key_shares: List[PrivateKeyShare]) -> List[int]:
    return [threshold_decrypt(x, private_key_shares) for x in l]


def encrypt_list(l: List[int], public_key: PublicKey) -> List[EncryptedNumber]:
    return [public_key.encrypt(x) for x in l]


class TestEliminateCandidateSet(unittest.TestCase):
    def test_01(self):
        """The test from the paper"""
        public_key, private_key_shares = keygen(n_bits=64, s=3, threshold=5, n_shares=9)

        candidates = [1, 2, 3]

        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([3, 1, 2], public_key), public_key.encrypt(8))
        ]
        for_elimination = [3]
        eliminated = eliminate_candidate_set(for_elimination, ballots, private_key_shares, public_key)

        self.assertEqual(len(ballots), len(eliminated), "The number of ballots must stay the same after elimination")

        self.assertListEqual([1, 2], eliminated[0].candidates, "The remaining candidates must be the not eliminated")

        self.assertListEqual([2, 1], decrypt_list(eliminated[0].preferences, private_key_shares), "Preferences must be right")

        self.assertEqual(8, threshold_decrypt(eliminated[0].weight, private_key_shares), "Weight must be right")

    def test_02(self):
        public_key, private_key_shares = keygen(n_bits=64, s=3, threshold=5, n_shares=9)

        candidates = [0, 1, 2, 3, 4, 5]

        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([0, 3, 4, 2, 1, 5], public_key), public_key.encrypt(8)),
            CandidateOrderBallot(candidates, encrypt_list([4, 2, 3, 5, 0, 1], public_key), public_key.encrypt(4)),

        ]
        for_elimination = [0, 3, 4]
        eliminated = eliminate_candidate_set(for_elimination, ballots, private_key_shares, public_key)

        self.assertEqual(len(ballots), len(eliminated), "The number of ballots must stay the same after elimination")

        self.assertListEqual([1, 2, 5], eliminated[0].candidates, "The remaining candidates must be the not eliminated")
        self.assertListEqual([1, 2, 5], eliminated[1].candidates, "The remaining candidates must be the not eliminated")

        self.assertListEqual([0, 1, 2], decrypt_list(eliminated[0].preferences, private_key_shares),
                             "Preferences must be right")
        self.assertListEqual([1, 2, 0], decrypt_list(eliminated[1].preferences, private_key_shares),
                             "Preferences must be right")

        self.assertEqual(8, threshold_decrypt(eliminated[0].weight, private_key_shares), "Weight must be right")
        self.assertEqual(4, threshold_decrypt(eliminated[1].weight, private_key_shares), "Weight must be right")


class TestComputeFirstPreferenceTallies(unittest.TestCase):
    def test_01(self):
        """Test from the paper"""
        public_key, private_key_shares = keygen(n_bits=64, s=3, threshold=5, n_shares=9)

        candidates = [1, 2, 3]
        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([3, 1, 2], public_key), public_key.encrypt(1))
        ]

        fpb, tallies = compute_first_preference_tallies(ballots, private_key_shares, public_key)

        self.assertListEqual([0, 1, 0], tallies, "The right tally counts")

        self.assertEqual(1, len(fpb), "The number of ballots must stay the same after computation")

        self.assertListEqual(candidates, fpb[0].candidates, "The right candidates")
        self.assertListEqual([0, 1, 0], decrypt_list(fpb[0].weights, private_key_shares),
                             "Weight 1 for first preference, 0 otherwise")

    def test_02(self):
        public_key, private_key_shares = keygen(n_bits=64, s=3, threshold=5, n_shares=9)

        candidates = [0, 1, 2, 3, 4, 5]

        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([0, 3, 4, 2, 1, 5], public_key), public_key.encrypt(80)),
            CandidateOrderBallot(candidates, encrypt_list([4, 2, 3, 5, 0, 1], public_key), public_key.encrypt(100)),
            CandidateOrderBallot(candidates, encrypt_list([5, 3, 0, 4, 2, 1], public_key), public_key.encrypt(100)),
            CandidateOrderBallot(candidates, encrypt_list([3, 2, 4, 5, 0, 1], public_key), public_key.encrypt(25)),
            CandidateOrderBallot(candidates, encrypt_list([2, 4, 3, 0, 1, 5], public_key), public_key.encrypt(25)),
        ]
        expected_tallies = [80, 0, 100, 25, 125, 0]

        fpb, tallies = compute_first_preference_tallies(ballots, private_key_shares, public_key)

        self.assertListEqual(expected_tallies, tallies, "The right tally counts")

        self.assertEqual(len(ballots), len(fpb), "The number of ballots must stay the same after computation")

        for i in range(len(ballots)):
            self.assertListEqual(candidates, fpb[i].candidates, "The right candidates")

        self.assertListEqual([80, 0, 0, 0, 0, 0], decrypt_list(fpb[0].weights, private_key_shares),
                             "Full weight for first preference, 0 otherwise")
        self.assertListEqual([0, 0, 0, 0, 100, 0], decrypt_list(fpb[1].weights, private_key_shares),
                             "Full weight for first preference, 0 otherwise")

    def test_03(self):
        public_key, private_key_shares = keygen(n_bits=64, s=3, threshold=5, n_shares=9)

        candidates = [0, 1, 2, 3, 4, 5]

        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([0, 3, 4, 2, 1, 5], public_key), public_key.encrypt(8)),
            CandidateOrderBallot(candidates, encrypt_list([4, 2, 3, 5, 0, 1], public_key), public_key.encrypt(10)),
            CandidateOrderBallot(candidates, encrypt_list([5, 3, 0, 4, 2, 1], public_key), public_key.encrypt(10)),
            CandidateOrderBallot(candidates, encrypt_list([3, 2, 4, 5, 0, 1], public_key), public_key.encrypt(2)),
            CandidateOrderBallot(candidates, encrypt_list([2, 4, 3, 0, 1, 5], public_key), public_key.encrypt(2)),
        ]
        expected_tallies = [8, 0, 10, 2, 12, 0]

        fpb, tallies = compute_first_preference_tallies(ballots, private_key_shares, public_key)

        self.assertListEqual(expected_tallies, tallies, "The right tally counts")

        self.assertEqual(len(ballots), len(fpb), "The number of ballots must stay the same after computation")

        for i in range(len(ballots)):
            self.assertListEqual(candidates, fpb[i].candidates, "The right candidates")

        self.assertListEqual([8, 0, 0, 0, 0, 0], decrypt_list(fpb[0].weights, private_key_shares),
                             "Full weight for first preference, 0 otherwise")
        self.assertListEqual([0, 0, 0, 0, 10, 0], decrypt_list(fpb[1].weights, private_key_shares),
                             "Full weight for first preference, 0 otherwise")


class TestReweighVotes(unittest.TestCase):
    def test_01(self):
        """Same as TestComputeFirstPreferenceTallies::test_03"""
        public_key, private_key_shares = keygen(n_bits=64, s=3, threshold=5, n_shares=9)

        candidates = [0, 1, 2, 3, 4, 5]

        ballots = [
            FirstPreferenceBallot(candidates, encrypt_list([0, 3, 4, 2, 1, 5], public_key),
                                  encrypt_list([8, 0, 0, 0, 0, 0], public_key)),
            FirstPreferenceBallot(candidates, encrypt_list([4, 2, 3, 5, 0, 1], public_key),
                                  encrypt_list([0, 0, 0, 0, 10, 0], public_key)),
            FirstPreferenceBallot(candidates, encrypt_list([5, 3, 0, 4, 2, 1], public_key),
                                  encrypt_list([0, 0, 10, 0, 0, 0], public_key)),
            FirstPreferenceBallot(candidates, encrypt_list([3, 2, 4, 5, 0, 1], public_key),
                                  encrypt_list([0, 0, 0, 0, 2, 0], public_key)),
            FirstPreferenceBallot(candidates, encrypt_list([2, 4, 3, 0, 1, 5], public_key),
                                  encrypt_list([0, 0, 0, 2, 0, 0], public_key)),
        ]

        tallies = [8, 0, 10, 2, 12, 0]
        q = 5
        elected = [0, 2, 4]
        cobs, d_lcm = reweight_votes(ballots, elected, q, tallies, public_key)

        self.assertEqual(120, d_lcm, "The right lowest common multiple")
        self.assertEqual(len(ballots), len(cobs), "The number of ballots must stay the same after computation")

        cand_f = [45, 120, 60, 120, 70, 120]  # factors for each candidate

        # weights must be equal to the original weight multiplied by the weight factor for the candidate that was the
        # first preference in that ballot
        expected_weights = [8 * cand_f[0], 10 * cand_f[4], 10 * cand_f[2], 2 * cand_f[4], 2 * cand_f[3]]

        self.assertEqual(expected_weights, [threshold_decrypt(cob.weight, private_key_shares) for cob in cobs], "Weights must be right")
        for i in range(len(ballots)):
            self.assertListEqual(candidates, cobs[i].candidates, "The right candidates")
            self.assertListEqual(decrypt_list(ballots[i].preferences, private_key_shares),
                                 decrypt_list(cobs[i].preferences, private_key_shares), "The right preferences")

    def test_02(self):
        public_key, private_key_shares = keygen(n_bits=64, s=3, threshold=5, n_shares=9)

        candidates = list(range(10))
        preferences = [
            [6, 8, 3, 2, 0, 9, 1, 4, 7, 5],
            [9, 6, 7, 0, 5, 2, 3, 4, 8, 1],
            [0, 5, 2, 9, 4, 8, 7, 6, 1, 3],
            [3, 1, 2, 0, 9, 4, 7, 8, 6, 5],
            [0, 5, 8, 6, 4, 3, 2, 9, 7, 1],
            [0, 7, 3, 2, 9, 6, 8, 4, 5, 1],
            [5, 0, 8, 1, 9, 6, 2, 7, 3, 4],
            [5, 2, 6, 0, 1, 9, 4, 3, 8, 7],
            [9, 6, 5, 3, 4, 7, 1, 8, 2, 0],
            [3, 8, 5, 4, 6, 2, 0, 7, 9, 1],
            [2, 5, 3, 7, 4, 1, 8, 6, 0, 9],
            [5, 1, 8, 7, 6, 4, 2, 0, 9, 3],
            [2, 1, 4, 7, 8, 9, 5, 0, 3, 6],
            [2, 3, 6, 7, 9, 1, 4, 5, 0, 8],
            [6, 2, 8, 7, 5, 4, 1, 3, 0, 9],
            [3, 0, 7, 8, 9, 1, 4, 6, 2, 5],
            [9, 8, 5, 0, 3, 4, 7, 6, 2, 1],
            [5, 3, 7, 4, 1, 8, 9, 2, 6, 0],
            [3, 5, 2, 7, 1, 8, 9, 0, 4, 6],
            [0, 2, 8, 7, 5, 3, 1, 4, 9, 6],
            [9, 3, 1, 5, 0, 6, 8, 4, 7, 2],
            [4, 3, 5, 2, 7, 8, 9, 1, 6, 0],
            [7, 3, 1, 5, 0, 6, 9, 2, 8, 4],
            [4, 2, 7, 8, 3, 0, 1, 6, 5, 9],
            [3, 2, 0, 9, 5, 1, 4, 7, 6, 8],
            [7, 4, 3, 6, 9, 2, 1, 8, 0, 5],
            [0, 8, 1, 6, 9, 7, 2, 3, 4, 5],
            [1, 7, 9, 0, 6, 5, 8, 3, 4, 2],
            [5, 7, 1, 3, 2, 4, 0, 6, 8, 9],
            [7, 1, 3, 9, 4, 0, 6, 2, 8, 5],
            [5, 3, 1, 8, 2, 0, 4, 6, 7, 9],
            [7, 6, 0, 1, 4, 3, 9, 5, 8, 2],
            [8, 4, 1, 6, 3, 2, 9, 5, 0, 7],
            [9, 4, 6, 8, 7, 3, 5, 0, 1, 2],
            [3, 5, 9, 6, 2, 1, 7, 8, 0, 4],
            [7, 2, 8, 9, 0, 5, 4, 1, 6, 3],
            [9, 1, 4, 3, 8, 6, 0, 2, 7, 5],
            [7, 0, 5, 1, 4, 3, 8, 9, 6, 2],
            [2, 8, 4, 1, 5, 3, 9, 7, 6, 0],
            [4, 1, 2, 6, 7, 5, 9, 8, 0, 3],
            [1, 2, 7, 3, 8, 4, 5, 6, 0, 9],
            [2, 6, 8, 5, 4, 1, 7, 3, 9, 0],
            [5, 2, 8, 0, 1, 7, 6, 9, 4, 3],
            [6, 2, 1, 4, 3, 9, 8, 0, 5, 7],
            [0, 2, 5, 7, 9, 4, 3, 8, 6, 1],
            [0, 7, 8, 1, 2, 5, 4, 9, 3, 6],
            [2, 9, 7, 4, 3, 0, 8, 1, 5, 6],
            [4, 2, 6, 3, 5, 8, 0, 7, 1, 9],
            [9, 4, 8, 0, 6, 2, 3, 7, 1, 5],
            [4, 3, 0, 9, 1, 7, 2, 8, 5, 6],
            [6, 4, 2, 3, 5, 0, 7, 9, 8, 1],
            [0, 1, 4, 8, 2, 6, 3, 5, 7, 9],
            [3, 9, 2, 8, 0, 5, 1, 4, 6, 7],
            [2, 1, 4, 0, 3, 6, 7, 8, 5, 9],
            [2, 8, 5, 7, 9, 3, 1, 4, 0, 6],
            [2, 4, 3, 8, 1, 7, 0, 6, 9, 5],
            [5, 6, 8, 7, 1, 2, 4, 9, 3, 0],
            [8, 3, 0, 9, 6, 5, 4, 2, 1, 7],
            [2, 3, 0, 7, 1, 5, 9, 4, 6, 8],
            [0, 5, 6, 2, 8, 9, 3, 7, 1, 4],
            [2, 7, 9, 6, 3, 5, 4, 8, 1, 0],
            [3, 8, 5, 4, 6, 1, 0, 9, 2, 7],
            [6, 4, 9, 3, 8, 2, 5, 0, 1, 7],
            [3, 6, 5, 0, 7, 9, 1, 2, 4, 8],
            [7, 9, 3, 8, 0, 6, 5, 2, 4, 1],
            [2, 4, 6, 0, 5, 9, 1, 8, 7, 3],
            [5, 3, 4, 6, 8, 9, 2, 7, 1, 0],
            [8, 1, 7, 5, 2, 9, 6, 0, 4, 3],
            [3, 1, 5, 6, 2, 7, 8, 4, 0, 9],
            [3, 8, 4, 5, 9, 6, 7, 1, 2, 0],
            [9, 6, 4, 2, 3, 1, 0, 8, 5, 7],
            [5, 0, 7, 8, 1, 3, 9, 4, 2, 6],
            [3, 6, 8, 5, 4, 9, 0, 1, 2, 7],
            [8, 0, 6, 7, 1, 2, 3, 5, 9, 4],
            [1, 5, 3, 9, 4, 7, 6, 0, 8, 2],
            [6, 8, 9, 1, 5, 7, 4, 2, 0, 3],
            [2, 1, 5, 0, 8, 3, 7, 9, 6, 4],
            [0, 4, 7, 5, 8, 1, 6, 3, 2, 9],
            [7, 6, 5, 3, 1, 0, 2, 9, 4, 8],
            [3, 0, 8, 1, 5, 2, 7, 9, 4, 6],
            [6, 9, 3, 8, 2, 7, 0, 5, 4, 1],
            [5, 9, 7, 3, 2, 8, 1, 4, 6, 0],
            [7, 0, 4, 3, 1, 2, 6, 9, 5, 8],
            [6, 9, 3, 8, 4, 5, 2, 1, 0, 7],
            [9, 7, 6, 8, 2, 5, 3, 4, 1, 0],
            [6, 8, 1, 7, 2, 4, 5, 3, 9, 0],
            [4, 6, 0, 1, 3, 9, 2, 8, 5, 7],
            [7, 2, 8, 3, 4, 9, 5, 6, 0, 1],
            [7, 3, 0, 8, 5, 1, 4, 6, 2, 9],
            [8, 2, 7, 6, 3, 4, 9, 1, 5, 0],
            [8, 3, 5, 7, 4, 2, 0, 9, 1, 6],
            [3, 6, 5, 1, 8, 2, 0, 9, 7, 4],
            [4, 9, 5, 8, 0, 1, 7, 6, 2, 3],
            [4, 5, 9, 8, 2, 1, 0, 3, 6, 7],
            [3, 2, 8, 9, 6, 5, 1, 0, 7, 4],
            [6, 1, 4, 2, 5, 3, 7, 9, 0, 8],
            [0, 5, 2, 3, 7, 6, 1, 4, 8, 9],
            [9, 3, 4, 1, 5, 6, 7, 0, 2, 8],
            [3, 0, 6, 7, 9, 2, 5, 8, 1, 4],
            [0, 1, 5, 2, 7, 3, 9, 4, 6, 8]
        ]
        tallies = [12, 8, 7, 11, 7, 6, 12, 10, 14, 13]
        ballots = [FirstPreferenceBallot(candidates, encrypt_list(prefs, public_key),
                                         [public_key.encrypt(1) if pref == 0 else public_key.encrypt(0) for pref in
                                          prefs]) for prefs in preferences]

        q = 12
        elected = [0, 6, 8]
        cobs, d_lcm = reweight_votes(ballots, elected, q, tallies, public_key)

        self.assertEqual(84, d_lcm, "The right lowest common multiple")
        self.assertEqual(len(ballots), len(cobs), "The number of ballots must stay the same after computation")

        cand_f = [0] + [84] * 5 + [0, 84, 12, 84]  # factors for each candidate

        # weights must be equal to the original weight (1 in this case for all ballots) multiplied by the weight factor
        # for the candidate that was the first preference in that ballot
        expected_weights = [cand_f[prefs.index(0)] for prefs in preferences]

        self.assertEqual(expected_weights, [threshold_decrypt(cob.weight, private_key_shares) for cob in cobs], "Weights must be right")
        for i in range(len(ballots)):
            self.assertListEqual(candidates, cobs[i].candidates, "The right candidates")
            self.assertListEqual(preferences[i],
                                 decrypt_list(cobs[i].preferences, private_key_shares), "The right preferences")


if __name__ == '__main__':
    unittest.main(verbosity=3)
