#!/usr/bin/env python3
"""
test.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains unit tests.

"""
import os
from secrets import randbelow
import sys
import unittest

from cryptovote.crypto import keygen
from cryptovote.damgard_jurik import keygen as keygen_dj, threshold_decrypt
from cryptovote.prime_gen import gen_prime
from cryptovote.shamir import Polynomial, reconstruct, share_secret


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


class TestShamir(unittest.TestCase):
    def test_polynomial(self):
        coeffs = [1, 2, 3, 4, 5]
        modulus = 23
        poly = Polynomial(coeffs, modulus)

        self.assertEqual(poly(0), coeffs[0])
        self.assertEqual(poly(1), sum(coeffs) % modulus)
        self.assertEqual(poly(5), sum([c_i * (5 ** i) for i, c_i in enumerate(coeffs)]) % modulus)

    # def test_reconstruct(self):
    #     for _ in range(10):
    #         modulus = gen_prime(b=32)
    #         secret = randbelow(modulus)
    #         coeffs = [secret] + [randbelow(modulus) for _ in range(randbelow(10) + 1)]
    #         poly = Polynomial(coeffs, modulus)
    #         threshold = len(coeffs)
    #
    #         shares = [(x, poly(x)) for x in range(1, threshold + randbelow(10))]
    #
    #         secret_prime = reconstruct(shares, modulus)
    #         print(coeffs)
    #
    #         self.assertEqual(secret, secret_prime)
    # #
    def test_shamir(self):
        for _ in range(10):
            modulus = gen_prime(b=32)
            print(modulus)
            secret = randbelow(modulus)
            n_shares = 5
            threshold = 4
            # n_shares = randbelow(4) + 1
            # threshold = randbelow(n_shares) + 1

            shares = share_secret(secret, modulus, threshold, n_shares)
            print(shares)
            secret_prime = reconstruct(shares, modulus)

            print(secret)
            print(secret_prime)
            print()
            self.assertEqual(secret, secret_prime)

# class TestDamgardJurik(unittest.TestCase):
#     def test_encrypt_decrypt(self):
#         public_key, private_key_shares = keygen_dj(n_bits=32, s=1, threshold=1, n_shares=2)


if __name__ == '__main__':
    unittest.main()
    #
    # print('keygen')
    # public_key, private_key_shares = keygen_dj(n_bits=32, s=2, threshold=2, n_shares=4)
    # print()
    #
    # print('message')
    # m = 1234
    # print(m)
    # print()
    #
    # print('encrypt')
    # c = public_key.encrypt(m)
    # print(c.value)
    # print()
    #
    # print('decrypt')
    # m_prime = threshold_decrypt(c, private_key_shares)
    # print(m_prime)
