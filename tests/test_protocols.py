import unittest

from cryptovote import CandidateOrderBallot, PrivateKey, PublicKey, eliminate_candidate_set
from phe import generate_paillier_keypair


def decrypt_list(l, private_key: PrivateKey):
    return [private_key.decrypt(x) for x in l]


def encrypt_list(l, public_key: PublicKey):
    return [public_key.encrypt(x) for x in l]


class TestEliminateCandidateSet(unittest.TestCase):
    def test_eliminateCandidateSet_01(self):
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

    def test_eliminateCandidateSet_02(self):
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

        self.assertListEqual([0, 1, 2], decrypt_list(eliminated[0].preferences, private_key), "Preferences must be right")
        self.assertListEqual([1, 2, 0], decrypt_list(eliminated[1].preferences, private_key), "Preferences must be right")

        self.assertEqual(0.8, private_key.decrypt(eliminated[0].weight), "Weight must be right")
        self.assertEqual(0.4, private_key.decrypt(eliminated[1].weight), "Weight must be right")