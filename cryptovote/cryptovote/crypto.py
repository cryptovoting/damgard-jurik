#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains a set of interfaces for interacting with cryptographic values
and functions, such as:
- Public and Private Keys
- Encrypted Number
- Key Generation, Encryption, and Decryption
- Homomorphic Operations

"""
from typing import Any, Tuple

from phe.paillier import EncryptedNumber as PaillierEncryptedNumber
from phe.paillier import generate_paillier_keypair, PaillierPrivateKey, PaillierPublicKey

from cryptovote.utils import powmod


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
            value=((self.value * other.value) % self.public_key.n_square)
        )

    def __radd__(self, other: Any) -> 'EncryptedNumber':
        return self.__add__(other)

    def __mul__(self, other: int) -> 'EncryptedNumber':
        if not isinstance(other, int):
            raise ValueError('Can only multiply an EncryptedNumber by an int')

        return EncryptedNumber(
            public_key=self.public_key,
            value=powmod(self.value, other, self.public_key.n_square)
        )

    def __rmul__(self, other: Any) -> 'EncryptedNumber':
        return self.__mul__(other)

    def __eq__(self, other):
        return self.value == other.value


# TODO: replace phe library with custom implementation
class PublicKey:
    def __init__(self, n: int):
        self.g = n + 1
        self.n = n
        self.n_square = n * n
        self._public_key = PaillierPublicKey(self.n)

    def encrypt(self, plaintext: int) -> EncryptedNumber:
        ciphertext = self._public_key.encrypt(plaintext)
        ciphertext = EncryptedNumber(public_key=self, value=ciphertext.ciphertext(be_secure=False))

        return ciphertext

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PublicKey):
            return False

        return self.n == other.n


class PrivateKey:
    def __init__(self, public_key: PublicKey, lam: int, mu: int):
        self.public_key = public_key
        self.lam = lam
        self.mu = mu
        self._public_key = PaillierPublicKey(self.public_key.n)
        self._private_key = PaillierPrivateKey(self._public_key, self.lam, self.mu)

    def decrypt(self, ciphertext: EncryptedNumber) -> int:
        plaintext = self._private_key.decrypt(PaillierEncryptedNumber(self._public_key, ciphertext.value))

        return plaintext


def keygen(n_bits: int = 2048) -> Tuple[PublicKey, PrivateKey]:
    _public_key, _private_key = generate_paillier_keypair(n_length=n_bits)
    public_key = PublicKey(_public_key.n)
    private_key = PrivateKey(public_key, _private_key.p, _private_key.q)

    return public_key, private_key
