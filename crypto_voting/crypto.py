#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains a set of interfaces for interacting with cryptographic values
and functions, such as:
- Plaintext and Ciphertext
- Public and Private Keys
- Key Generation, Encryption, and Decryption
- Homomorphic Operations

"""
from abc import ABC
from typing import Tuple

from phe.paillier import EncryptedNumber, generate_paillier_keypair, PaillierPrivateKey, PaillierPublicKey


class Text(ABC):
    """ Abstract class for plaintext and ciphertext. """
    def __init__(self, value: int):
        self.value = value

    def __repr__(self) -> str:
        return str(self.value)


class Plaintext(Text):
    """ Plaintext. """
    pass


class Ciphertext(Text):
    """ Ciphertext. """
    pass


# TODO: replace phe library with custom implementation
class PublicKey:
    def __init__(self, n: int):
        self.g = n + 1
        self.n = n
        self._public_key = PaillierPublicKey(self.n)

    def encrypt(self, plaintext: Plaintext) -> Ciphertext:
        ciphertext = self._public_key.encrypt(plaintext.value)
        ciphertext = Ciphertext(ciphertext.ciphertext())

        return ciphertext


class PrivateKey:
    def __init__(self, public_key: PublicKey, lam: int, mu: int):
        self.public_key = public_key
        self.lam = lam
        self.mu = mu
        self._public_key = PaillierPublicKey(self.public_key.n)
        self._private_key = PaillierPrivateKey(self._public_key, self.lam, self.mu)

    def decrypt(self, ciphertext: Ciphertext) -> Plaintext:
        plaintext = self._private_key.decrypt(EncryptedNumber(self._public_key, ciphertext.value))
        plaintext = Plaintext(plaintext)

        return plaintext


def keygen(n_bits: int = 2048) -> Tuple[PublicKey, PrivateKey]:
    _public_key, _private_key = generate_paillier_keypair(n_length=n_bits)
    public_key = PublicKey(_public_key.n)
    private_key = PrivateKey(public_key, _private_key.p, _private_key.q)

    return public_key, private_key
