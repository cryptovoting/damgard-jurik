import unittest

from cryptovote import CandidateOrderBallot, PrivateKey, PublicKey, eliminate_candidate_set, \
    compute_first_preference_tallies
from phe import generate_paillier_keypair


def decrypt_list(l, private_key: PrivateKey):
    return [private_key.decrypt(x) for x in l]


def encrypt_list(l, public_key: PublicKey):
    return [public_key.encrypt(x) for x in l]


class TestEliminateCandidateSet(unittest.TestCase):
    def test_01(self):
        """The test from the paper"""
        public_key, private_key = generate_paillier_keypair()

        candidates = [1, 2, 3]

        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([3, 1, 2], public_key), public_key.encrypt(0.8))
        ]
        for_elimination = [3]
        eliminated = eliminate_candidate_set(for_elimination, ballots, private_key, public_key)

        self.assertEqual(len(ballots), len(eliminated), "The number of ballots must stay the same after elimination")

        self.assertListEqual([1, 2], eliminated[0].candidates, "The remaining candidates must be the not eliminated")

        self.assertListEqual([2, 1], decrypt_list(eliminated[0].preferences, private_key), "Preferences must be right")

        self.assertEqual(0.8, private_key.decrypt(eliminated[0].weight), "Weight must be right")

    def test_02(self):
        public_key, private_key = generate_paillier_keypair()

        candidates = [0, 1, 2, 3, 4, 5]

        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([0, 3, 4, 2, 1, 5], public_key), public_key.encrypt(0.8)),
            CandidateOrderBallot(candidates, encrypt_list([4, 2, 3, 5, 0, 1], public_key), public_key.encrypt(0.4)),

        ]
        for_elimination = [0, 3, 4]
        eliminated = eliminate_candidate_set(for_elimination, ballots, private_key, public_key)

        self.assertEqual(len(ballots), len(eliminated), "The number of ballots must stay the same after elimination")

        self.assertListEqual([1, 2, 5], eliminated[0].candidates, "The remaining candidates must be the not eliminated")
        self.assertListEqual([1, 2, 5], eliminated[1].candidates, "The remaining candidates must be the not eliminated")

        self.assertListEqual([0, 1, 2], decrypt_list(eliminated[0].preferences, private_key),
                             "Preferences must be right")
        self.assertListEqual([1, 2, 0], decrypt_list(eliminated[1].preferences, private_key),
                             "Preferences must be right")

        self.assertEqual(0.8, private_key.decrypt(eliminated[0].weight), "Weight must be right")
        self.assertEqual(0.4, private_key.decrypt(eliminated[1].weight), "Weight must be right")


class TestComputeFirstPreferenceTallies(unittest.TestCase):
    def test_01(self):
        """Test from the paper"""
        public_key, private_key = generate_paillier_keypair()

        candidates = [1, 2, 3]
        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([3, 1, 2], public_key), public_key.encrypt(1.0))
        ]

        fpb, tallies = compute_first_preference_tallies(ballots, private_key, public_key)

        self.assertListEqual([0, 1, 0], tallies, "The right tally counts")

        self.assertEqual(1, len(fpb), "The number of ballots must stay the same after computation")

        self.assertListEqual(candidates, fpb[0].candidates, "The right candidates")
        self.assertListEqual([0, 1, 0], decrypt_list(fpb[0].weights, private_key),
                             "Weight 1.0 for first preference, 0 otherwise")

    def test_02(self):
        public_key, private_key = generate_paillier_keypair()

        candidates = [0, 1, 2, 3, 4, 5]

        ballots = [
            CandidateOrderBallot(candidates, encrypt_list([0, 3, 4, 2, 1, 5], public_key), public_key.encrypt(0.8)),
            CandidateOrderBallot(candidates, encrypt_list([4, 2, 3, 5, 0, 1], public_key), public_key.encrypt(1.0)),
            CandidateOrderBallot(candidates, encrypt_list([5, 3, 0, 4, 2, 1], public_key), public_key.encrypt(1.0)),
            CandidateOrderBallot(candidates, encrypt_list([3, 2, 4, 5, 0, 1], public_key), public_key.encrypt(0.25)),
            CandidateOrderBallot(candidates, encrypt_list([2, 4, 3, 0, 1, 5], public_key), public_key.encrypt(0.25)),
        ]
        expected_talies = [0.8, 0, 1, 0.25, 1.25, 0]

        fpb, tallies = compute_first_preference_tallies(ballots, private_key, public_key)

        self.assertListEqual(expected_talies, tallies, "The right tally counts")

        self.assertEqual(len(ballots), len(fpb), "The number of ballots must stay the same after computation")

        for i in range(len(ballots)):
            self.assertListEqual(candidates, fpb[i].candidates, "The right candidates")

        self.assertListEqual([0.8, 0, 0, 0, 0, 0], decrypt_list(fpb[0].weights, private_key),
                             "Full weight for first preference, 0 otherwise")
        self.assertListEqual([0, 0, 0, 0, 1, 0], decrypt_list(fpb[1].weights, private_key),
                             "Full weight for first preference, 0 otherwise")

        pass
