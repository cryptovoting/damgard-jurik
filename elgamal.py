from functools import reduce
from operator import mul
import random
from typing import List, Tuple

from gmpy2 import mpz


def keygen():
    raise NotImplementedError


def encrypt(message: mpz, generator: mpz, q_prime: mpz, public_key: mpz) -> Tuple[mpz, mpz]:
    # TODO: use os.urandom instead (ex. struct.unpack('I', os.urandom(4))[0])
    r = random.randint(1, q_prime - 1)
    c1 = generator ** r
    c2 = (public_key ** r) * message
    ciphertext = (c1, c2)

    return ciphertext


def decrypt(ciphertext: Tuple[mpz, mpz], secret_keys: List[mpz]) -> mpz:
    c1, c2 = ciphertext
    plaintext = c2 / reduce(mul, [c1 ** secret_key for secret_key in secret_keys])

    return plaintext
