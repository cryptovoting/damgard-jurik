#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Implementation of Shamir secret sharing.
"""
from secrets import randbelow
from typing import List, Tuple

from gmpy2 import mpq, mpz


class Polynomial:
    def __init__(self, coeffs: List[int], modulus: int):
        self.coeffs = [mpz(c_i) for c_i in coeffs]
        self.modulus = mpz(modulus)

    def __call__(self, x: int) -> int:
        x = mpz(x)
        f_x = mpz(0)

        for i, c_i in enumerate(self.coeffs):
            f_x = (f_x + c_i * pow(x, i, self.modulus) % self.modulus) % self.modulus

        return f_x


def share_secret(secret: int,
                 modulus: int,
                 threshold: int,
                 n_shares: int) -> List[Tuple[int, int]]:
    """ Computes shares of a secret modulo m.

    Generates n_shares shares of the secret. Any threshold shares can decrypt the secret.
    """
    assert threshold > 0
    assert n_shares >= threshold

    coeffs = [secret] + [randbelow(modulus) for _ in range(threshold - 1)]
    print(coeffs)
    f = Polynomial(coeffs, modulus)
    X = [mpz(x) for x in range(1, n_shares + 1)]
    shares = [(x, f(x)) for x in X]

    return shares


def reconstruct(shares: List[Tuple[int, int]],
                modulus: int) -> int:
    """ Reconstructs a secret from shares."""
    # Convert to mpz
    shares = [(mpz(x), mpz(f_x)) for x, f_x in shares]
    modulus = mpz(modulus)

    # Reconstruct secret
    secret = mpz(0)
    for i, (x_i, f_x_i) in enumerate(shares):
        product = mpz(1)
        for j, (x_j, _) in enumerate(shares):
            if i != j:
                product = product * mpq(-1 * x_j, x_i - x_j) % modulus
        secret = (secret + f_x_i * product % modulus) % modulus

    return secret
