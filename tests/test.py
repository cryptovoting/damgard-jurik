#!/usr/bin/env python3
"""
test.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains unit tests for the damgard-jurik package.

"""
from secrets import randbelow
import unittest

from damgard_jurik import keygen
from damgard_jurik.prime_gen import gen_prime
from damgard_jurik.shamir import Polynomial, reconstruct, share_secret


class TestShamir(unittest.TestCase):
    def test_polynomial(self):
        coeffs = [1, 2, 3, 4, 5]
        modulus = 23
        poly = Polynomial(coeffs, modulus)

        self.assertEqual(poly(0), coeffs[0])
        self.assertEqual(poly(1), sum(coeffs) % modulus)
        self.assertEqual(poly(5), sum([c_i * (5 ** i) for i, c_i in enumerate(coeffs)]) % modulus)

    def test_shamir(self):
        for _ in range(10):
            modulus = gen_prime(n_bits=32)
            secret = randbelow(modulus)
            n_shares = randbelow(20) + 1
            threshold = randbelow(n_shares) + 1

            shares = share_secret(secret, modulus, threshold, n_shares)
            secret_prime = reconstruct(shares, modulus)

            self.assertEqual(secret, secret_prime)


class TestDamgardJurik(unittest.TestCase):
    def test_encrypt_decrypt(self):
        for _ in range(10):
            n_bits = randbelow(32) + 16
            s = randbelow(5) + 1
            threshold = randbelow(10) + 1
            n_shares = 2 * threshold + randbelow(10)

            public_key, private_key_ring = keygen(n_bits=n_bits, s=s, threshold=threshold, n_shares=n_shares)

            m = randbelow(public_key.n_s)

            c = public_key.encrypt(m)
            m_prime = private_key_ring.decrypt(c)

            self.assertEqual(m, m_prime)


class TestDamgardJurikHomomorphic(unittest.TestCase):
    def setUp(self):
        self.public_key, self.private_key_ring = keygen(n_bits=64, s=3, threshold=5, n_shares=9)

    def test_homomorphic_add(self):
        for _ in range(10):
            plaintext_1, plaintext_2 = randbelow(100), randbelow(100)

            ciphertext_1, ciphertext_2 = self.public_key.encrypt(plaintext_1), self.public_key.encrypt(plaintext_2)
            ciphertext = ciphertext_1 + ciphertext_2
            decrypted_plaintext = self.private_key_ring.decrypt(ciphertext)

            self.assertNotEqual(plaintext_1, ciphertext_1.value)
            self.assertNotEqual(plaintext_2, ciphertext_2.value)
            self.assertEqual(plaintext_1 + plaintext_2, decrypted_plaintext)

    def test_homomorphic_multiply(self):
        for _ in range(10):
            plaintext = randbelow(100)
            scalar = randbelow(100)

            ciphertext = self.public_key.encrypt(plaintext)
            ciphertext = ciphertext * scalar
            decrypted_plaintext = self.private_key_ring.decrypt(ciphertext)

            self.assertNotEqual(plaintext, ciphertext.value)
            self.assertEqual(plaintext * scalar, decrypted_plaintext)

    def test_homomorphic_divide(self):
        for _ in range(10):
            scalar = randbelow(100) + 1
            multiple = randbelow(100) + 1
            plaintext = scalar * multiple

            ciphertext = self.public_key.encrypt(plaintext)
            ciphertext = ciphertext / scalar
            decrypted_plaintext = self.private_key_ring.decrypt(ciphertext)

            self.assertNotEqual(plaintext, ciphertext.value)
            self.assertEqual(plaintext // scalar, decrypted_plaintext)


if __name__ == '__main__':
    unittest.main()
