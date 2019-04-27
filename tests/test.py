#!/usr/bin/env python3
"""
test.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains unit tests.

"""
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cryptovote.cryptovote.crypto import keygen


class TestCrypto(unittest.TestCase):
    def test_encrypt_decrypt(self):
        public_key, private_key = keygen(n_bits=2048)
        plaintext = 100

        ciphertext = public_key.encrypt(plaintext)
        decrypted_plaintext = private_key.decrypt(ciphertext)

        self.assertNotEqual(plaintext, ciphertext.value)
        self.assertEqual(plaintext, decrypted_plaintext)

    def test_homomorphic_add(self):
        public_key, private_key = keygen(n_bits=2048)
        plaintext_1, plaintext_2 = 20, 53

        ciphertext_1, ciphertext_2 = public_key.encrypt(plaintext_1), public_key.encrypt(plaintext_2)
        ciphertext = ciphertext_1 + ciphertext_2
        decrypted_plaintext = private_key.decrypt(ciphertext)

        self.assertNotEqual(plaintext_1, ciphertext_1.value)
        self.assertNotEqual(plaintext_2, ciphertext_2.value)
        self.assertEqual(plaintext_1 + plaintext_2, decrypted_plaintext)

    def test_homomorphic_multiply(self):
        public_key, private_key = keygen(n_bits=2048)
        plaintext, scalar = 44, 20

        ciphertext = public_key.encrypt(plaintext)
        ciphertext = ciphertext * scalar
        decrypted_plaintext = private_key.decrypt(ciphertext)

        self.assertNotEqual(plaintext, ciphertext.value)
        self.assertEqual(plaintext * scalar, decrypted_plaintext)


if __name__ == '__main__':
    unittest.main()
