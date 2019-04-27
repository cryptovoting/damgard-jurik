import unittest

from crypto_voting.ballots import Ballot


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


if __name__ == '__main__':
    unittest.main(verbosity=3)
