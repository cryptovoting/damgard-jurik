#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Implementation of Shamir secret sharing.
"""
from secrets import randbelow
from typing import List, Tuple

from gmpy2 import mpz

from damgard_jurik.utils import int_to_mpz, inv_mod


class Polynomial:
    """Represents a polynomial in a finite field."""

    @int_to_mpz
    def __init__(self, coeffs: List[int], modulus: int):
        """Initializes the polynomial.

        :param coeffs: The coefficients of x^0, x^1, x^2, ...
        :param modulus: The modulus of the field the polynomial is in.
        """
        self.coeffs = [mpz(c_i) for c_i in coeffs]
        self.modulus = modulus

    @int_to_mpz
    def __call__(self, x: int) -> int:
        """Computes f(x) where f is this polynomial.

        :param x: The input to the polynomial.
        :return: The integer f(x) where f is this polynomial.
        """
        f_x = mpz(0)

        for i, c_i in enumerate(self.coeffs):
            f_x = (f_x + c_i * pow(x, mpz(i), self.modulus) % self.modulus) % self.modulus

        return f_x


@int_to_mpz
def share_secret(secret: int,
                 modulus: int,
                 threshold: int,
                 n_shares: int) -> List[Tuple[int, int]]:
    """Computes shares of a secret using Shamir secret sharing.

    :param secret: The secret to be shared.
    :param modulus: The modulus used when sharing the secret.
    :param threshold: The minimum number of shares that will be needed to reconstruct the secret.
    :param n_shares: The number of shares to create.
    :return: A list of shares of the secret, where each share is the tuple (x, f(x)) and where f(0) is the secret.
    """
    # Ensure valid parameters
    if not (0 <= secret < modulus):
        raise ValueError('The secret must be between 0 and modulus - 1')

    if n_shares < threshold:
        raise ValueError('The number of shares must be at least as large as the threshold')

    if threshold < 1:
        raise ValueError('The threshold and number of shares must be at least 1')

    # Create the polynomial that will be used to share the secret (f(0) = secret)
    coeffs = [secret] + [randbelow(modulus) for _ in range(threshold - 1)]
    f = Polynomial(coeffs, modulus)

    # Use the polynomial to share the secret
    X = [mpz(x) for x in range(1, n_shares + 1)]
    shares = [(x, f(x)) for x in X]

    return shares


@int_to_mpz
def reconstruct(shares: List[Tuple[int, int]],
                modulus: int) -> int:
    """Reconstructs a secret from shares.

    Assumes the shares are unique and there are at least as many shares as the required threshold.

    :param shares: Shares of a secret.
    :param modulus: The modulus used when sharing the secret.
    :return: The secret.
    """
    # Convert to mpz
    shares = [(mpz(x), mpz(f_x)) for x, f_x in shares]

    # Reconstruct secret
    secret = mpz(0)
    for i, (x_i, f_x_i) in enumerate(shares):
        product = mpz(1)

        for j, (x_j, _) in enumerate(shares):
            if i != j:
                product = product * x_j * inv_mod(x_j - x_i, modulus) % modulus

        secret = (secret + f_x_i * product % modulus) % modulus

    return secret
