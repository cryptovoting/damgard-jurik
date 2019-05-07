#!/usr/bin/env python3
"""
utils.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains useful utility functions.

"""
from functools import wraps
from typing import Callable, List, Tuple

from gmpy2 import mpz


def int_to_mpz(func: Callable) -> Callable:
    """ Converts all int arguments to mpz."""
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        return func(*[mpz(arg) if isinstance(arg, int) else arg for arg in args],
                    **{key: mpz(value) if isinstance(value, int) else value for key, value in kwargs.items()})
    return func_wrapper


def prod(nums: List[int]) -> int:
    """ Returns nums[0] * num[1] * ..."""
    product = mpz(1)

    for num in nums:
        product *= num

    return product


@int_to_mpz
def gcd(a: int, b: int) -> int:
    """ Find the greatest common divisor of two integers. """
    return a if b == 0 else gcd(b, a % b)


@int_to_mpz
def lcm(a: int, b: int) -> int:
    """ Find the least common multiple of two integers. """
    return a * b // gcd(a, b)


@int_to_mpz
def pow_mod(a: int, b: int, m: int) -> int:
    """ Computes a^b (mod m)."""
    if b < 0:
        a = inv_mod(a, m)
        b = -b

    return pow(a, b, m)


@int_to_mpz
def extended_euclidean(a: int, b: int) -> Tuple[int, int]:
    """ Uses the Extended Euclidean Algorithm to compute x and y s.t. ax + by = gcd(a, b)

    https://en.wikibooks.org/wiki/Algorithm_Implementation/Mathematics/Extended_Euclidean_algorithm#Python
    """
    if a == 0:
        return mpz(0), mpz(1)

    y, x = extended_euclidean(b % a, a)
    x = x - (b // a) * y

    return x, y


@int_to_mpz
def inv_mod(a: int, m: int) -> int:
    """ Finds the inverse of a modulo m (i.e. b s.t. a*b = 1 (mod m))."""
    if a < 0:
        a = m + a

    # a and m must be coprime to find an inverse
    if gcd(a, m) != 1:
        raise Exception(f'modular inverse does not exist since {a} and {m} are not coprime')

    x, _ = extended_euclidean(a, m)
    x_inv = x % m

    return x_inv


def crm(a_list: List[int], n_list: List[int]) -> int:
    """ Applies the Chinese Remainder Theorem.

    Finds the unique x such that x = a_i (mod n_i) for all i.
    """
    a_list = [mpz(a_i) for a_i in a_list]
    n_list = [mpz(n_i) for n_i in n_list]

    N = prod(n_list)
    y_list = [N // n_i for n_i in n_list]
    z_list = [inv_mod(y_i, n_i) for y_i, n_i in zip(y_list, n_list)]
    x = sum(a_i * y_i * z_i for a_i, y_i, z_i in zip(a_list, y_list, z_list))

    return x
