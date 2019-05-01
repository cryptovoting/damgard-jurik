#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains an implementation of the Damgard-Jurik threshold decryption scheme.
https://people.csail.mit.edu/rivest/voting/papers/DamgardJurikNielsen-AGeneralizationOfPailliersPublicKeySystemWithApplicationsToElectronicVoting.pdf
"""
from functools import lru_cache
from math import factorial
from secrets import randbelow
from typing import Any, List, Tuple

from cryptovote.prime_gen import gen_safe_prime_pair
from cryptovote.shamir import share_secret
from cryptovote.utils import crm, inv_mod, pow_mod


class EncryptedNumber:
    def __init__(self, public_key: 'PublicKey', value: int):
        self.public_key = public_key
        self.value = value

    def __add__(self, other: Any) -> 'EncryptedNumber':
        if not isinstance(other, EncryptedNumber):
            raise ValueError('Can only add an EncryptedNumber to another EncryptedNumber')

        if self.public_key != other.public_key:
            raise ValueError("Attempted to add numbers encrypted against different public keys!")

        return EncryptedNumber(
            public_key=self.public_key,
            value=((self.value * other.value) % self.public_key.n_s_1)
        )

    def __radd__(self, other: Any) -> 'EncryptedNumber':
        return self.__add__(other)

    def __mul__(self, other: int) -> 'EncryptedNumber':
        if not isinstance(other, int):
            raise ValueError('Can only multiply an EncryptedNumber by an int')

        return EncryptedNumber(
            public_key=self.public_key,
            value=pow(self.value, other, self.public_key.n_s_1)
        )

    def __rmul__(self, other: Any) -> 'EncryptedNumber':
        return self.__mul__(other)

    def __eq__(self, other):
        return self.value == other.value


class PublicKey:
    def __init__(self, n: int, s: int, threshold: int, delta: int):
        self.n = n
        self.s = s
        self.n_s = self.n ** self.s  # n^s
        self.n_s_1 = self.n_s * self.n  # n^(s+1)
        self.threshold = threshold
        self.delta = delta

    def encrypt(self, m: int) -> EncryptedNumber:
        # Choose random r in Z_n^*
        r = randbelow(self.n - 1) + 1
        c = pow(1 + self.n, m, self.n_s_1) * pow(r, self.n_s, self.n_s_1) % self.n_s_1
        c = EncryptedNumber(self, c)

        return c


class PrivateKeyShare:
    def __init__(self, public_key: PublicKey, i: int, s_i: int, delta: int):
        self.public_key = public_key
        self.i = i
        self.s_i = s_i
        self.delta = delta

    def decrypt(self, c: EncryptedNumber) -> int:
        c_i = pow(c.value, 2 * self.delta * self.s_i, self.public_key.n_s_1)

        return c_i


def keygen(n_bits: int = 2048,
           s: int = 4,
           threshold: int = 9,
           n_shares: int = 16) -> Tuple[PublicKey, List[PrivateKeyShare]]:
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
    public_key = PublicKey(n=n, s=s, threshold=threshold, delta=delta)
    private_key_shares = [PrivateKeyShare(public_key=public_key, i=i, s_i=s_i, delta=delta) for i, s_i in shares]

    return public_key, private_key_shares


def damgard_jurik_reduce(a: int, s: int, n: int) -> int:
    """ Computes i given a = (1 + n)^i (mod n^(s+1))."""
    def L(b: int) -> int:
        assert((b-1)%n == 0)
        return (b - 1)//n

    @lru_cache(s)
    def n_pow(p: int) -> int:
        return n ** p

    @lru_cache(s)
    def fact(k: int) -> int:
        return factorial(k)

    i = 0
    for j in range(1, s+1):
        t_1 = L(a % n_pow(j + 1))
        t_2 = i

        for k in range(2, j+1):
            i = i - 1
            t_2 = t_2 * i % n_pow(j)
            #assert(t_2*n_pow(k-1)%fact(k) == 0)
            t_1 = (t_1 - (t_2 * n_pow(k - 1) * inv_mod(fact(k), n_pow(j))))% n_pow(j)

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
    threshold, delta, s, n, n_s, n_s_1 = \
        c.public_key.threshold, c.public_key.delta, c.public_key.s, c.public_key.n, c.public_key.n_s, c.public_key.n_s_1

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

    print("c_list", c_list)

    # Define lambda function
    def lam(i: int) -> int:
        S_prime = S - {i}
        l = delta
        print("Finding lambda for", i)
        for i_prime in S - {i}:
            assert l % (i - i_prime) == 0
            l = l // (i - i_prime)
        l = l * (-1 if len(S_prime) % 2 != 0 else 1) * pow(i, len(S_prime))
        print("which is", l)
        return l

    # Decrypt
    c_prime = 1
    for c_i, i in zip(c_list, i_list):
        c_prime = (c_prime * pow_mod(c_i, (2 * lam(i)), n_s_1)) % n_s_1
    
    print("c_prime", c_prime)

    print("n_s", n_s)
    print("n_s_1", n_s_1)

    m = (damgard_jurik_reduce(c_prime, s, n) * inv_mod(4 * (delta ** 2), n_s_1))%n_s_1

    return m
