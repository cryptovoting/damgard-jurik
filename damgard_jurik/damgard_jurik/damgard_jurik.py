#!/usr/bin/env python3
"""
crypto.py
Boucher, Govedič, Saowakon, Swanson 2019

Contains an implementation of the Damgard-Jurik threshold decryption scheme.

"""
from functools import lru_cache
from math import factorial
from secrets import randbelow
from typing import Any, List, Tuple

from gmpy2 import mpz

from damgard_jurik.prime_gen import gen_safe_prime_pair
from damgard_jurik.shamir import share_secret
from damgard_jurik.utils import int_to_mpz, crm, inv_mod, pow_mod


class EncryptedNumber:
    """Represents a number encrypted with a PublicKey."""

    @int_to_mpz
    def __init__(self, value: int, public_key: 'PublicKey'):
        """Initializes the EncryptedNumber.

        :param value: The encrypted number.
        :param public_key: The public key used to encrypt `value`.
        """
        self.value = value
        self.public_key = public_key

    def __add__(self, other: Any) -> 'EncryptedNumber':
        """Adds two EncryptedNumbers.

        Applies the appropriate operations such that the result
        is an EncryptedNumber that decrypts to the sum of the
        the decryption of this number and the decryption of `other`.

        :param other: An EncryptedNumber.
        :return: An EncryptedNumber containing the sum of this number and `other`.
        """
        if not isinstance(other, EncryptedNumber):
            raise ValueError('Can only add/subtract an EncryptedNumber to another EncryptedNumber')

        if self.public_key != other.public_key:
            raise ValueError("Attempted to add/subtract numbers encrypted against different public keys!")

        return EncryptedNumber(
            value=((self.value * other.value) % self.public_key.n_s_1),
            public_key=self.public_key
        )

    def __radd__(self, other: Any) -> 'EncryptedNumber':
        """See `__add__`."""
        return self.__add__(other)

    def __sub__(self, other: Any) -> 'EncryptedNumber':
        """Subtracts two EncryptedNumbers.

        Applies the appropriate operations such that the result
        is an EncryptedNumber that decrypts to the difference of the
        the decryption of this number and the decryption of `other`.

        :param other: An EncryptedNumber.
        :return: An EncryptedNumber containing the difference of this number and `other`.
        """
        if not isinstance(other, EncryptedNumber):
            raise ValueError('Can only add/subtract an EncryptedNumber from another EncryptedNumber')

        if self.public_key != other.public_key:
            raise ValueError("Attempted to add/subtract numbers encrypted against different public keys!")

        # Multiply other by -1 via inv_mod
        other_inv = EncryptedNumber(
            value=inv_mod(other.value, other.public_key.n_s_1),
            public_key=other.public_key
        )

        return self.__add__(other_inv)

    def __rsub__(self, other: Any) -> 'EncryptedNumber':
        """See `__sub__`."""
        # Multiply self by -1 via inv_mod
        self_inv = EncryptedNumber(
            value=inv_mod(self.value, self.public_key.n_s_1),
            public_key=self.public_key
        )

        return self_inv.__add__(other)

    @int_to_mpz
    def __mul__(self, other: int) -> 'EncryptedNumber':
        """Multiplies an EncryptedNumber by a scalar.

        Applies the appropriate operations such that the result
        is an EncryptedNumber that decrypts to the product of the
        the decryption of this number and `other`.

        :param other: An integer.
        :return: An EncryptedNumber containing the product of this number and `other`.
        """
        return EncryptedNumber(
            public_key=self.public_key,
            value=pow(self.value, other, self.public_key.n_s_1)
        )

    @int_to_mpz
    def __rmul__(self, other: int) -> 'EncryptedNumber':
        """See `__mul__`."""
        return self.__mul__(other)

    @int_to_mpz
    def __truediv__(self, other: int):
        """Divides an EncryptedNumber by a scalar.

        Applies the appropriate operations such that the result
        is an EncryptedNumber that decrypts to the quotient of the
        the decryption of this number divided by `other`.

        :param other: An integer.
        :return: An EncryptedNumber containing the quotient of this number and `other`.
        """
        return self * inv_mod(other, self.public_key.n_s_1)

    def __eq__(self, other: Any):
        """Returns whether this EncryptedNumber is equal to `other`.

        Two EncryptedNumbers are equal when their values and PublicKeys are the same.

        Note: Two EncryptedNumbers containing encryptions of the same plaintext which
        were encrypted using the same PublicKey can still be not equal due to
        randomness in the encryption process.

        :param other: An EncryptedNumber.
        :return: True if this EncryptedNumber is equal to `other`, False otherwise.
        """
        return isinstance(other, EncryptedNumber) and self.value == other.value and self.public_key == other.public_key


class PublicKey:
    """Represents a Damgard-Jurik public key."""

    @int_to_mpz
    def __init__(self, n: int, s: int, m: int, threshold: int, delta: int):
        """Initializes the PublicKey and performs pre-computations.

        :param n: The product of safe primes `p` and `q` generated during `keygen`.
        :param s: The power to which `n` is raised.
        :param m: The product of Sophie Germain primes `p_prime` and `q_prime` generated during `keygen`.
        :param threshold: The minimum number of (unique) PrivateKeyShares needed to decrypt an EncryptedNumber.
        :param delta: The factorial of the number of PrivateKeyShares generated.
        """
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
        """Encrypts a number.

        :param m: The plaintext to be encrypted.
        :return: An EncryptedNumber containing the encryption of `m`.
        """
        # Choose random r in Z_n^*
        r = mpz(randbelow(self.n - 1)) + 1
        c = pow(self.n + 1, m, self.n_s_1) * pow(r, self.n_s, self.n_s_1) % self.n_s_1

        return EncryptedNumber(value=c, public_key=self)

    def encrypt_list(self, m_list: List[int]) -> List[EncryptedNumber]:
        """Encrypts each number in a list.

        :param m_list: A list of plaintexts to be encrypted.
        :return: A list containing an EncryptedNumber for each plaintext in `m_list`.
        """
        return [self.encrypt(m) for m in m_list]

    def __eq__(self, other: Any) -> bool:
        """Returns whether this PublicKey is equal to `other`.

        Two PublicKeys are equal when all attributes initialized in `__init__` are the same.

        :param other: A PublicKey.
        :return: True if this PublicKey is equal to `other`, False otherwise.
        """
        if not isinstance(other, PublicKey):
            return False

        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Hashes this PublicKey.

        The hash is a hash of a tuple of all attributes initialized in `__init__`.

        :return: An integer representing the hash of this PublicKey.
        """
        return hash(tuple(sorted(self.__dict__.items())))


class PrivateKeyShare:
    @int_to_mpz
    def __init__(self, public_key: PublicKey, i: int, s_i: int):
        """Initializes the PrivateKeyShare and performs pre-computations.

        :param public_key: The PublicKey corresponding to this PrivateKeyShare.
        :param i: The x value of this share generated using a polynomial via Shamir secret sharing.
        :param s_i: The y=f(i) value of this share generated using a polynomial via Shamir secret sharing.
        """
        self.public_key = public_key
        self.i = i
        self.s_i = s_i
        self.two_delta_s_i = 2 * self.public_key.delta * self.s_i

    def decrypt(self, c: EncryptedNumber) -> int:
        """Partially decrypts an EncryptedNumber.

        :param c: An EncryptedNumber.
        :return: An integer containing this PrivateKeyShare's portion of the decryption of `c`.
        """
        return pow(c.value, self.two_delta_s_i, self.public_key.n_s_1)

    def __eq__(self, other: Any) -> bool:
        """Returns whether this PrivateKeyShare is equal to `other`.

        Two PrivateKeyShares are equal when all attributes initialized in `__init__` are the same.

        :param other: A PrivateKeyShare.
        :return: True if this PrivateKeyShare is equal to `other`, False otherwise.
        """
        if not isinstance(other, PrivateKeyShare):
            return False

        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Hashes this PrivateKeyShare.

        The hash is a hash of a tuple of all attributes initialized in `__init__`.

        :return: An integer representing the hash of this PrivateKeyShare.
        """
        return hash(tuple(sorted(self.__dict__.items())))


@int_to_mpz
def damgard_jurik_reduce(a: int, s: int, n: int) -> int:
    """Computes i given a = (1 + n)^i (mod n^(s+1)).

    :param a: The integer a in the above equation.
    :param s: The integer s in the above equation.
    :param n: The integer n in the above equation.
    :return: The integer i in the above equation.
    """
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


class PrivateKeyRing:
    def __init__(self, private_key_shares: List[PrivateKeyShare]):
        """Initializes the PrivateKeyRing, checks that enough PrivateKeyShares are provided, and performs pre-computations.

        :param private_key_shares: A list of PrivateKeyShares.
        """
        if len(private_key_shares) == 0:
            raise ValueError('Must have at least one PrivateKeyShare')

        if len({pks.public_key for pks in private_key_shares}) > 1:
            raise ValueError('PrivateKeyShares do not have the same public key')

        public_key = private_key_shares[0].public_key
        private_key_shares = set(private_key_shares)

        if len(private_key_shares) < public_key.threshold:
            raise ValueError('Number of unique PrivateKeyShares is less than the threshold to decrypt')

        self.public_key = public_key
        self.private_key_shares = list(private_key_shares)[:self.public_key.threshold]
        self.i_list = [pks.i for pks in self.private_key_shares]
        self.S = set(self.i_list)
        self.inv_four_delta_squared = inv_mod(4 * (self.public_key.delta ** 2), self.public_key.n_s)

    def decrypt(self, c: EncryptedNumber) -> int:
        """Decrypts an EncryptedNumber.

        :param c: An EncryptedNumber.
        :return: An integer containing the decryption of `c`.
        """
        # Use PrivateKeyShares to decrypt
        c_list = [pk.decrypt(c) for pk in self.private_key_shares]

        # Define lambda function
        @int_to_mpz
        def lam(i: int) -> int:
            S_prime = self.S - {i}
            l = self.public_key.delta % self.public_key.n_s_m

            for i_prime in S_prime:
                l = l * i_prime * inv_mod(i_prime - i, self.public_key.n_s_m) % self.public_key.n_s_m

            return l

        # Decrypt
        c_prime = mpz(1)
        for c_i, i in zip(c_list, self.i_list):
            c_prime = (c_prime * pow_mod(c_i, (2 * lam(i)), self.public_key.n_s_1)) % self.public_key.n_s_1

        c_prime = damgard_jurik_reduce(c_prime, self.public_key.s, self.public_key.n)
        m = c_prime * self.inv_four_delta_squared % self.public_key.n_s

        return m

    def decrypt_list(self, c_list: List[EncryptedNumber]) -> List[int]:
        """Decrypts each number in a list.

        :param c_list: A list of EncryptedNumbers to be decrypted.
        :return: A list containing the decryption of each EncryptedNumber in `c_list`.
        """
        return [self.decrypt(c) for c in c_list]


def keygen(n_bits: int = 64,
           s: int = 1,
           threshold: int = 3,
           n_shares: int = 3) -> Tuple[PublicKey, PrivateKeyRing]:
    """Generates a PublicKey and a PrivateKeyRing using the threshold variant of Damgard-Jurik.

    The PublicKey is a single key which can be used to encrypt numbers
    while the PrivateKeyRing contains a number of PrivateKeyShares which
    must be used together to decrypt encrypted numbers.

    :param n_bits: The number of bits to use in the public and private keys.
    :param s: The power to which n = p * q will be raised. Plaintexts live in Z_n^s.
    :param threshold: The minimum number of PrivateKeyShares needed to decrypt an encrypted number.
    :param n_shares: The number of PrivateKeyShares to generate.
    :return: A tuple containing the generated PublicKey and PrivateKeyRing.
    """
    # Ensure valid parameters
    if n_bits < 16:  # Note: 16 is somewhat arbitrary
        raise ValueError('Minimum number of bits for encryption is 16')

    if s < 1:
        raise ValueError('s must be greater than 1')

    if n_shares < threshold:
        raise ValueError('The number of shares must be at least as large as the threshold')

    if threshold < 1:
        raise ValueError('The threshold and number of shares must be at least 1')

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
    private_key_shares = [PrivateKeyShare(public_key=public_key, i=i, s_i=s_i) for i, s_i in shares]
    private_key_ring = PrivateKeyRing(private_key_shares=private_key_shares)

    return public_key, private_key_ring
