#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains a set of interfaces for interacting with cryptographic values
and functions, such as:
- Plaintext and Ciphertext
- Encryption and Decryption
- Homomorphic Operations

"""
from abc import ABC

class Text(ABC):
    """ Abstract class for plaintext and ciphertext. """
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.text


class Plaintext(Text):
    """ Plaintext. """
    pass


class Ciphertext(Text):
    """ Ciphertext. """
    pass
