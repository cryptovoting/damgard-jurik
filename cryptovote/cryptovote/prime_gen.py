#!/usr/bin/env python3
"""
prime_gen.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains methods for generating prime numbers.

"""
from random import randint
from typing import Tuple


def is_prime(p: int) -> bool:
    """ Returns whether p is probably prime.

    This should run enough iterations of the test to be reasonably confident that p is prime.
    """
    for a in range(2, 10):
        if pow(a, p - 1, p) != 1:
            return False
    return True


def gen_prime(b: int) -> int:
    """ Returns a prime p with b bits."""
    while True:
        p = randint(2 ** (b - 1), 2 ** b - 1)
        if is_prime(p):
            return p


def gen_safe_prime(b: int) -> int:
    """ Return a safe prime p with b bits."""
    while True:
        q = gen_prime(b - 1)
        if is_prime(q):
            p = 2 * q + 1
            if is_prime(p):
                return p


def gen_safe_prime_pair(b: int) -> Tuple[int, int]:
    """ Return a pair of safe primes with b bits."""
    p = gen_safe_prime(b)
    q = gen_safe_prime(b)
    while p == q:
        q = gen_safe_prime(b)

    return p, q
