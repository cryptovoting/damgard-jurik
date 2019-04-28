#!/usr/bin/env python3
"""
utils.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains useful utility functions.

"""


def powmod(a: int, b: int, m: int) -> int:
    """ Returns the power a**b % m. """
    if b == 1:
        return a % m
    if b % 2 == 0:
        return powmod(a ** 2 % m, b // 2, m) % m
    return (a * powmod(a ** 2 % m, (b - 1) // 2, m)) % m

def gcd(a: int, b: int) -> int:
    """ Find the greatest common divisor of two integers. """
    return a if b == 0 else gcd(b, a%b)

def lcm(a: int, b: int) -> int:
    """ Find the least common multiple of two integers. """
    return a*b/gcd(a, b)