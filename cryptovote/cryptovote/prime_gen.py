#!/usr/bin/env python3
"""
prime_gen.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains methods for generating prime numbers.

"""
from secrets import randbelow
from typing import Tuple

from cryptovote.utils import int_to_mpz


@int_to_mpz
def is_prime(p: int) -> bool:
    """ Returns whether p is probably prime.

    This should run enough iterations of the test to be reasonably confident that p is prime.
    """
    # TODO: how many iterations?
    for a in range(2, 6):
        if pow(a, p - 1, p) != 1:
            return False

    return True


@int_to_mpz
def gen_prime(b: int) -> int:
    """ Returns a prime p with b bits."""
    base = 2 ** (b - 1)

    while True:
        p = base + randbelow(base)

        if is_prime(p):
            return p


@int_to_mpz
def gen_safe_prime(b: int) -> int:
    """ Return a safe prime p with b bits."""
    while True:
        q = gen_prime(b - 1)

        if is_prime(q):
            p = 2 * q + 1

            if is_prime(p):
                return p


@int_to_mpz
def gen_safe_prime_pair(b: int) -> Tuple[int, int]:
    """ Return a pair of safe primes with b bits."""
    p = gen_safe_prime(b)
    q = gen_safe_prime(b)

    while p == q:
        q = gen_safe_prime(b)

    return p, q
