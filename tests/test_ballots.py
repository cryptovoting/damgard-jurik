import unittest

from cryptovote.ballots import Ballot, CandidateOrderBallot, FirstPreferenceBallot, CandidateEliminationBallot
from cryptovote.crypto import generate_paillier_keypair


class TestBallots(unittest.TestCase):
    def test_shuffle(self):
        lists = [
            [0, 1, 2, 3, 4, 5, 6],
            [10, 11, 12, 13, 14, 15, 16],
            ['0', '1', '2', '3', '4', '5', '6']
        ]

        # it is a random function so we must test it more than once

        for _ in range(5):
            result = Ballot.shuffle(lists[0], lists[1], lists[2])

            for i in range(3):
                l_r = result[i]
                l = lists[i]
                self.assertEqual(len(l_r), len(l), "Length of the outputted list must be the same")
                self.assertSetEqual(set(l_r), set(l), "The outputted list must still contain the same elements")

            expected_1 = [10 + i for i in result[0]]
            expected_2 = [str(i) for i in result[0]]

            self.assertEqual(result[1], expected_1,
                             "Elements in the second list must maintain their relative order to the first one")
            self.assertEqual(result[2], expected_2,
                             "Elements in the third list must maintain their relative order to the first one")


class TestCandidateOrderBallot(unittest.TestCase):
    def test_toFirstPreferenceBallot_01(self):
        public_key, private_key = generate_paillier_keypair()

        candidates = [1, 2, 3]
        preferences = [3, 1, 2]
        weight = 1.0
        first_preferences = [0, weight, 0]

        ballot = CandidateOrderBallot(candidates[:], [public_key.encrypt(pref) for pref in preferences], public_key.encrypt(weight))

        result = ballot.to_first_preference(private_key, public_key)

        self.assertIsInstance(result, FirstPreferenceBallot, "The returned ballot must be of type FirstPreferenceBallot")

        self.assertListEqual(result.candidates, candidates, "The candidates list must match")

        self.assertListEqual([private_key.decrypt(preference) for preference in result.preferences], preferences, "The preferences list must match")

        self.assertListEqual([private_key.decrypt(weight) for weight in result.weights], first_preferences, "The weights list must match")

    def test_toFirstPreferenceBallot_02(self):
        public_key, private_key = generate_paillier_keypair()

        candidates = [0, 1, 2, 3, 4, 5]
        preferences = [1, 5, 0, 2, 4, 3]
        weight = 0.8
        first_preferences = [0, 0, weight, 0, 0, 0]

        ballot = CandidateOrderBallot(candidates[:], [public_key.encrypt(pref) for pref in preferences],
                                       public_key.encrypt(weight))

        result = ballot.to_first_preference(private_key, public_key)

        self.assertIsInstance(result, FirstPreferenceBallot, "The returned ballot must be of type FirstPreferenceBallot")

        self.assertListEqual(result.candidates, candidates, "The candidates list must match")

        self.assertListEqual([private_key.decrypt(preference) for preference in result.preferences], preferences, "The preferences list must match")

        self.assertListEqual([private_key.decrypt(weight) for weight in result.weights], first_preferences, "The weights list must match")

    def test_toCandidateElimination_01(self):
        public_key, private_key = generate_paillier_keypair()

        candidates = [1, 2, 3]
        preferences = [3, 1, 2]
        weight = 1.0
        eliminated = [0, 0, 1]
        post_eliminated = [0, 1, 0]
        
        ballot = CandidateOrderBallot(candidates[:], [public_key.encrypt(pref) for pref in preferences],
                                       public_key.encrypt(weight))

        result = ballot.to_candidate_elimination(eliminated, private_key, public_key)

        self.assertIsInstance(result, CandidateEliminationBallot, "The returned ballot must be of type CandidateEliminationBallot")

        self.assertListEqual([private_key.decrypt(preference) for preference in result.preferences], sorted(preferences), "The preferences list must match")

        self.assertListEqual([private_key.decrypt(eliminated_i) for eliminated_i in result.eliminated], post_eliminated, "The eliminated list must match")

        self.assertEqual(private_key.decrypt(result.weight), weight, "The weight must match")


class TestCandidateEliminationBallot(unittest.TestCase):
    def test_toCandidateOrderBallot_01(self):
        public_key, private_key = generate_paillier_keypair()

        candidates = [1, 2, 3]
        preferences = [3, 1, 2]
        weight = 1.0
        eliminated = [0, 0, 1]
        post_eliminated = [0, 1, 0]

        ballot = CandidateEliminationBallot([public_key.encrypt(cand) for cand in candidates], [public_key.encrypt(pref) for pref in preferences],[public_key.encrypt(elim) for elim in post_eliminated],
                                      public_key.encrypt(weight))

        result = ballot.to_candidate_order(private_key, public_key)

        self.assertIsInstance(result, CandidateOrderBallot,
                              "The returned ballot must be of type CandidateOrderBallot")

        self.assertListEqual([private_key.decrypt(preference) for preference in result.preferences], preferences)

        self.assertListEqual(result.candidates, candidates, "The candidates lists must match")

        self.assertEqual(private_key.decrypt(result.weight), weight, "The weight must match")

if __name__ == '__main__':
    unittest.main(verbosity=3)
