#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Implementation of Shamir secret sharing.
"""
from secrets import randbelow
from typing import List, Tuple


def share_secret(secret: int,
                 modulus: int,
                 threshold: int,
                 n_shares: int) -> List[Tuple[int, int]]:
    """ Computes shares of a secret modulo m.

    Generates n_shares shares of the secret. Any threshold shares can decrypt the secret.
    """
    coeffs = [secret] + [randbelow(modulus) for _ in range(threshold)]

    def f(x: int) -> int:
        return sum(a_i * (x ** i) for i, a_i in enumerate(coeffs)) % modulus

    shares = [(x, f(x)) for x in range(1, n_shares + 1)]

    return shares
