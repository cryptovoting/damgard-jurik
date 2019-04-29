#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains an implementation of the Damgard-Jurik threshold decryption scheme.
https://people.csail.mit.edu/rivest/voting/papers/DamgardJurikNielsen-AGeneralizationOfPailliersPublicKeySystemWithApplicationsToElectronicVoting.pdf
"""
from typing import List, Tuple

from cryptovote.prime_gen import gen_safe_prime_pair


class PublicKey:
    pass


class PrivateKeyShare:
    pass


def keygen(n_bits: int = 2048,
           s: int = 4,
           n_shares: int = 16) -> Tuple[PublicKey, List[PrivateKeyShare]]:
    p, q = gen_safe_prime_pair(n_bits)
    p_prime, q_prime = (p - 1) // 2, (q - 1) // 2
    n, m = p * q, p_prime * q_prime

