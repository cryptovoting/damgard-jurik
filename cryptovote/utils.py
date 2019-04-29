#!/usr/bin/env python3
"""
utils.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains useful utility functions.

"""
from functools import reduce
from operator import mul
from typing import List, Tuple


def prod(nums: List[int]) -> int:
    return reduce(mul, nums)


def gcd(a: int, b: int) -> int:
    """ Find the greatest common divisor of two integers. """
    return a if b == 0 else gcd(b, a % b)


def lcm(a: int, b: int) -> int:
    """ Find the least common multiple of two integers. """
    return a * b // gcd(a, b)


def pow_mod(a: int, b: int, m: int) -> int:
    """ Returns the power a**b % m. """
    if b == 1:
        return a % m
    if b % 2 == 0:
        return pow_mod(a ** 2 % m, b // 2, m) % m
    return (a * pow_mod(a ** 2 % m, (b - 1) // 2, m)) % m


# https://en.wikibooks.org/wiki/Algorithm_Implementation/Mathematics/Extended_Euclidean_algorithm#Python
def extended_euclidean(a: int, b: int) -> Tuple[int, int]:
    """ Uses the Extended Euclidean Algorithm to compute x and y s.t. ax + by = gcd(a, b)"""
    if a == 0:
        return 0, 1

    y, x = extended_euclidean(b % a, a)
    x = x - (b // a) * y

    return x, y


def inv_mod(a: int, m: int) -> int:
    """ Finds the inverse of a modulo m."""
    # a and m must be coprime to find an inverse
    if gcd(a, m) == 1:
        raise Exception(f'modular inverse does not exist since {a} and {m} are not coprime')

    x, _ = extended_euclidean(a, m)
    x_inv = x % m

    return x_inv


def crm(a_list: List[int], n_list: List[int]) -> int:
    """ Applies the Chinese Remainder Theorem.

    Finds the unique x such that x = a_i (mod n_i) for all i.
    """
    N = prod(n_list)
    y_list = [N // n_i for n_i in n_list]
    z_list = [inv_mod(y_i, n_i) for y_i, n_i in zip(y_list, n_list)]
    x = sum(a_i * y_i * z_i for a_i, y_i, z_i in zip(a_list, y_list, z_list))

    return x
