#!/usr/bin/env python3
"""
prime_gen.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains methods for generating prime numbers.

"""
from secrets import randbits
from typing import Tuple

try:
    try:
        from gmpy2 import bit_set, is_prime, next_prime
    except ImportError:
        from gmpy import bit_set, is_prime, next_prime
except ImportError:
    GMP_AVAILABLE = False
else:
    GMP_AVAILABLE = True

if (not GMP_AVAILABLE):
    try:
        from Cryptodome.Util.number import isPrime as is_prime
        from Cryptodome.Util.number import getPrime as crypto_prime
    except ImportError:
        from Crypto.Util.number import isPrime as is_prime
        from Crypto.Util.number import getPrime as crypto_prime

def gmp_prime(n_bits: int) -> int:
    """Returns a prime number with `n_bits` bits.

    :param n_bits: The number of bits the prime number should contain.
    :return: A prime number with `n_bits` bits.
    """
    base = randbits(n_bits)
    base = bit_set(base, n_bits - 1)
    p = next_prime(base)

    return p

if (GMP_AVAILABLE):
    gen_prime = gmp_prime
else:
    def gen_prime (n_bits: int) -> int:
        return crypto_prime(n_bits)


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

            if (GMP_AVAILABLE):
                if is_prime(p):
                    return p
            else:
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
