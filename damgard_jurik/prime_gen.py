#!/usr/bin/env python3
"""
prime_gen.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains methods for generating prime numbers.

"""
from secrets import randbits
from typing import Tuple

from gmpy2 import bit_set, is_prime, next_prime


def gen_prime(n_bits: int) -> int:
    """Returns a prime number with `n_bits` bits.

    :param n_bits: The number of bits the prime number should contain.
    :return: A prime number with `n_bits` bits.
    """
    base = randbits(n_bits)
    base = bit_set(base, n_bits - 1)
    p = next_prime(base)

    return p


def gen_safe_prime(n_bits: int) -> int:
    """Returns a safe prime p with `n_bits` bits.

    A safe prime is a prime p = 2 * q + 1 where q is also a prime.

    :param n_bits: The number of bits the prime number should contain.
    :return: A safe prime with `n_bits` bits.
    """
    while True:
        q = gen_prime(n_bits - 1)

        if is_prime(q):
            p = 2 * q + 1

            if is_prime(p):
                return p


def gen_safe_prime_pair(n_bits: int) -> Tuple[int, int]:
    """Returns a pair of two different safe primes with `n_bits` bits.

    :param n_bits: The number of bits the prime number should contain.
    :return: A tuple of two different safe primes, each with `n_bits` bits.
    """
    p = gen_safe_prime(n_bits)
    q = gen_safe_prime(n_bits)

    while p == q:
        q = gen_safe_prime(n_bits)

    return p, q
