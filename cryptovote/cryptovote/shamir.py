#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Implementation of Shamir secret sharing.
"""
from secrets import randbelow
from typing import List, Tuple


class Polynomial:
    def __init__(self, coeffs: List[int], modulus: int):
        self.coeffs = coeffs
        self.modulus = modulus

    def __call__(self, x: int):
        f_x = 0
        for i, a_i in enumerate(self.coeffs):
            f_x += a_i * pow(x, i, self.modulus) % self.modulus
            f_x = f_x % self.modulus

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
    f = Polynomial(coeffs, modulus)
    shares = [(x, f(x)) for x in range(1, n_shares + 1)]

    return shares


def get_unique_shares(shares: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """ Returns a list of unique shares (i.e. (x, f(x)) pairs with unique x)."""
    i_set = set()
    unique_shares = []
    for share in shares:
        i = share[0]

        if i not in i_set:
            unique_shares.append(share)
            i_set.add(i)

    return unique_shares


def reconstruct(shares: List[Tuple[int, int]],
                threshold: int) -> int:
    """ Reconstructs a secret from shares."""
    shares = get_unique_shares(shares)

    if not len(shares) >= threshold:
        raise ValueError(f'Need at least {threshold} unique PrivateKeyShares to decrypt but only have {len(shares)}.')

    secret = 0
    for i, (x_i, f_x_i) in enumerate(shares):
        product = 1
        for j, (x_j, _) in enumerate(shares):
            if i != j:
                product = product * (-1 * x_j) / (x_i - x_j)
        secret += f_x_i * product

    return secret
