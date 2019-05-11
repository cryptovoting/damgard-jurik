#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains an implementation of the Damgard-Jurik threshold decryption scheme.
https://people.csail.mit.edu/rivest/voting/papers/DamgardJurikNielsen-AGeneralizationOfPailliersPublicKeySystemWithApplicationsToElectronicVoting.pdf
"""
from functools import lru_cache
from math import factorial
from multiprocessing import Pool
from secrets import randbelow
from typing import Any, List, Tuple

from gmpy2 import mpz

from cryptovote.prime_gen import gen_safe_prime_pair
from cryptovote.shamir import share_secret
from cryptovote.utils import int_to_mpz, crm, inv_mod, pow_mod


class EncryptedNumber:
    def __init__(self, public_key: 'PublicKey', value: int):
        self.public_key = public_key
        self.value = mpz(value)

    def __add__(self, other: Any) -> 'EncryptedNumber':
        if not isinstance(other, EncryptedNumber):
            raise ValueError('Can only add/subtract an EncryptedNumber to another EncryptedNumber')

        if self.public_key != other.public_key:
            raise ValueError("Attempted to add/subtract numbers encrypted against different public keys!")

        return EncryptedNumber(
            public_key=self.public_key,
            value=((self.value * other.value) % self.public_key.n_s_1)
        )

    def __radd__(self, other: Any) -> 'EncryptedNumber':
        return self.__add__(other)

    def __sub__(self, other: Any) -> 'EncryptedNumber':
        if not isinstance(other, EncryptedNumber):
            raise ValueError('Can only add/subtract an EncryptedNumber from another EncryptedNumber')

        if self.public_key != other.public_key:
            raise ValueError("Attempted to add/subtract numbers encrypted against different public keys!")

        # Multiply other by -1 via inv_mod
        other_inv = EncryptedNumber(other.public_key, inv_mod(other.value, other.public_key.n_s_1))

        return self.__add__(other_inv)

    def __rsub__(self, other: Any) -> 'EncryptedNumber':
        # Multiply self by -1 via inv_mod
        self_inv = EncryptedNumber(self.public_key, inv_mod(self.value, self.public_key.n_s_1))

        return self_inv.__add__(other)

    @int_to_mpz
    def __mul__(self, other: int) -> 'EncryptedNumber':
        return EncryptedNumber(
            public_key=self.public_key,
            value=pow(self.value, other, self.public_key.n_s_1)
        )

    @int_to_mpz
    def __rmul__(self, other: int) -> 'EncryptedNumber':
        return self.__mul__(other)

    @int_to_mpz
    def __truediv__(self, other: int):
        return self * inv_mod(other, self.public_key.n_s_1)

    def __eq__(self, other: Any):
        return isinstance(other, EncryptedNumber) and self.value == other.value


class PublicKey:
    @int_to_mpz
    def __init__(self, n: int, s: int, m: int, threshold: int, delta: int):
        self.n = n
        self.s = s
        self.m = m
        self.n_s = self.n ** self.s  # n^s
        self.n_s_1 = self.n_s * self.n  # n^(s+1)
        self.n_s_m = self.n_s * self.m  # n^s * m
        self.threshold = threshold
        self.delta = delta

    @int_to_mpz
    def encrypt(self, m: int) -> EncryptedNumber:
        # Choose random r in Z_n^*
        r = mpz(randbelow(self.n - 1)) + 1
        c = pow(self.n + 1, m, self.n_s_1) * pow(r, self.n_s, self.n_s_1) % self.n_s_1
        c = EncryptedNumber(self, c)

        return c

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PublicKey):
            return False

        return self.__dict__ == other.__dict__


class PrivateKeyShare:
    @int_to_mpz
    def __init__(self, public_key: PublicKey, i: int, s_i: int, delta: int):
        self.public_key = public_key
        self.i = i
        self.s_i = s_i
        self.delta = delta
        self.two_delta_s_i = 2 * self.delta * self.s_i

    def decrypt(self, c: EncryptedNumber) -> int:
        c_i = pow(c.value, self.two_delta_s_i, self.public_key.n_s_1)

        return c_i

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PrivateKeyShare):
            return False

        return self.__dict__ == other.__dict__


@int_to_mpz
def keygen(n_bits: int = 2048,
           s: int = 3,
           threshold: int = 5,
           n_shares: int = 9) -> Tuple[PublicKey, List[PrivateKeyShare]]:
    """ Generates a PublicKey and a list of PrivateKeyShares using Damgard-Jurik threshold variant."""
    # Find n = p * q and m = p_prime * q_prime where p = 2 * p_prime + 1 and q = 2 * q_prime + 1
    p, q = gen_safe_prime_pair(n_bits)
    p_prime, q_prime = (p - 1) // 2, (q - 1) // 2
    n, m = p * q, p_prime * q_prime

    # Pre-compute for convenience
    n_s = n ** s
    n_s_m = n_s * m

    # Find d such that d = 0 mod m and d = 1 mod n^s
    d = crm(a_list=[0, 1], n_list=[m, n_s])

    # Use Shamir secret sharing to share_secret d
    shares = share_secret(
        secret=d,
        modulus=n_s_m,
        threshold=threshold,
        n_shares=n_shares
    )

    # Create PublicKey and PrivateKeyShares
    delta = factorial(n_shares)
    public_key = PublicKey(n=n, s=s, m=m, threshold=threshold, delta=delta)
    private_key_shares = [PrivateKeyShare(public_key=public_key, i=i, s_i=s_i, delta=delta) for i, s_i in shares]

    return public_key, private_key_shares

@int_to_mpz
def damgard_jurik_reduce(a: int, s: int, n: int) -> int:
    """ Computes i given a = (1 + n)^i (mod n^(s+1))."""
    def L(b: int) -> int:
        assert (b - 1) % n == 0
        return (b - 1) // n

    @lru_cache(int(s))
    @int_to_mpz
    def n_pow(p: int) -> int:
        return n ** p

    @lru_cache(int(s))
    @int_to_mpz
    def fact(k: int) -> int:
        return mpz(factorial(k))

    i = mpz(0)
    for j in range(1, s + 1):
        j = mpz(j)

        t_1 = L(a % n_pow(j + 1))
        t_2 = i

        for k in range(2, j + 1):
            k = mpz(k)

            i = i - 1
            t_2 = t_2 * i % n_pow(j)
            t_1 = t_1 - (t_2 * n_pow(k - 1) * inv_mod(fact(k), n_pow(j))) % n_pow(j)

        i = t_1

    return i


def get_unique_private_key_shares(private_key_shares: List[PrivateKeyShare]) -> List[PrivateKeyShare]:
    """ Returns a list of unique PrivateKeyShares (i.e. (i, f(i)) pairs with unique i)."""
    i_set = set()
    unique_private_key_shares = []

    for pk in private_key_shares:
        if pk.i not in i_set:
            unique_private_key_shares.append(pk)
            i_set.add(pk.i)

    return unique_private_key_shares


def threshold_decrypt(c: EncryptedNumber, private_key_shares: List[PrivateKeyShare]) -> int:
    """ Performs threshold decryption using a list of PrivateKeyShares."""
    # Extract values from PublicKey
    threshold, delta, s, n, n_s, n_s_1, n_s_m = \
        c.public_key.threshold, c.public_key.delta, c.public_key.s, c.public_key.n, c.public_key.n_s, c.public_key.n_s_1, c.public_key.n_s_m

    # Get unique PrivateKeyShares
    private_key_shares = get_unique_private_key_shares(private_key_shares)

    if not len(private_key_shares) >= threshold:
        raise ValueError(f'Need at least {threshold} unique PrivateKeyShares to decrypt but only have {len(private_key_shares)}.')

    # Only need threshold PrivateKeyShares to decrypt
    private_key_shares = private_key_shares[:threshold]
    S = {pk.i for pk in private_key_shares}

    # Use PrivateKeyShares to decrypt
    c_list = [pk.decrypt(c) for pk in private_key_shares]
    i_list = [pk.i for pk in private_key_shares]

    # Define lambda function
    @int_to_mpz
    def lam(i: int) -> int:
        S_prime = S - {i}
        l = delta % n_s_m

        for i_prime in S_prime:
            l = l * i_prime * inv_mod(i_prime - i, n_s_m) % n_s_m

        return l

    # Decrypt
    c_prime = mpz(1)
    for c_i, i in zip(c_list, i_list):
        c_prime = (c_prime * pow_mod(c_i, (2 * lam(i)), n_s_1)) % n_s_1
    
    m = damgard_jurik_reduce(c_prime, s, n) * inv_mod(4 * (delta ** 2), n_s) % n_s

    return m


def encrypt_list(m_list: List[int],
                 public_key: PublicKey,
                 parallel: bool = True) -> List[EncryptedNumber]:
    pass


def threshold_decrypt_list(c_list: List[EncryptedNumber],
                           private_key_shares: List[PrivateKeyShare],
                           parallel: bool = True) -> List[int]:
    pass
