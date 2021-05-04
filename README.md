# Damgard-Jurik

An implementation of the threshold variant of the [Damgard-Jurik](https://people.csail.mit.edu/rivest/voting/papers/DamgardJurikNielsen-AGeneralizationOfPailliersPublicKeySystemWithApplicationsToElectronicVoting.pdf) homomorphic encryption cryptosystem.

## Table of Contents

* [Installation](#installation)
* [Public and Private Keys](#public-and-private-keys)
* [Key Generation](#key-generation)
* [Encryption and Decryption](#encryption-and-decryption)
* [Homomorphic Operations](#homomorphic-operations)

## Installation

Requires Python 3.6+.

```bash
pip install damgard-jurik
```

Alternatively, the code can be cloned and installed locally as follows.

```bash
git clone https://github.com/cryptovoting/damgard-jurik.git
cd damgard-jurik
pip install -e .
```
*Note that the `-e` flag will instruct pip to install the package as "editable". That is, when changes are made to any part of the package during development, those changes will immediately be available system-wide on the activated python environment.*

For best performance, [install gmpy2](https://gmpy2.readthedocs.io/en/latest/intro.html#installation).

All requirements for this package should be added to `setup.py`.

## Public and Private Keys

In the threshold variant of Damgard-Jurik implemented in this repository, a key pair consists of single public key along with a private key that has been split into multiple components using [Shamir's secret sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing). The public key encrypts messages while the shares of the private key all contribute a portion of the decryption without ever requiring reconstruction of the private key. Thus, trust is distributed among the holders of the private key shares.

In this implementation, the public key is a `PublicKey` object with an encrypt function while the private key shares are `PrivateKeyShare` objects with a decrypt function that performs a partial decryption using that share of the private key. A `PrivateKeyRing` object holds a set of `PrivateKeyShare`s and contains a decrypt function that calls each `PrivateKeyShare`'s decrypt function and combines the results to obtain the final decryption.

## Key Generation

To generate a `PublicKey` and the corresponding `PrivateKeyRing`, run the following commands:

```python
from damgard_jurik import keygen

public_key, private_key_ring = keygen(
    n_bits=64,
    s=1,
    threshold=3,
    n_shares=3
)
```

The parameters to `keygen` are as follows:

- `n_bits`: The number of bits of encryption used in the public key and private key shares.
- `s`: The exponent to which the public key parameter `n` is raised (where `n = p * q` is the product of two `n_bits`-bit primes `p` and `q`.). Plaintexts are integers in the space `Z_n^s = {0, 1, ..., n^s - 1}`.
- `threshold`: The minimum number of private key shares needed to decrypt an encrypted message.
- `n_shares`: The number of private key shares to generate.


## Encryption and Decryption

Encryption and decryption are implemented as methods of the `PublicKey` and `PrivateKeyRing` classes, respectively.

For example:

```python
m = 42
c = public_key.encrypt(m)
m_prime = private_key_ring.decrypt(c)
# m_prime = 42
```

Plaintexts like `m` are simply Python integers while ciphertexts (encrypted plaintexts) like `c` are instances of the `EncryptedNumber` class. `EncryptedNumber` objects contain an encryption of the plaintext along with a reference to the `PublicKey` used to encrypt the plaintext.

Additionally, the `PublicKey` and `PrivateKingRing` classes have a convenience method for encrypting and decrypting lists of integers, as shown below.

```python
m_list = [42, 33, 100]
c_list = public_key.encrypt_list(m_list)
m_prime_list = private_key_ring.decrypt_list(c_list)
# m_prime_list = [42, 33, 100]
```

## Homomorphic Operations

Due to the additively homomorphic nature of the Damgard-Jurik cryptosystem, ciphertexts can be combined in such a way as to obtain an encryption of the sum of the associated plaintexts. Futhermore, ciphertexts can be combined with un-encrypted integers in such a way as to obtain the product of the associated plaintext and the un-encrypted integer. For convenience, the `EncryptedNumber` class has overridden the `+`, `-`, `*`, and `/` operators to implement these operations.

For example:

```python
m_1, m_2 = 42, 33
c_1, c_2 = public_key.encrypt(m_1), public_key.encrypt(m_2)
c = c_1 + c_2
m_prime = private_key_ring.decrypt(c)
# m_prime = 75 = 42 + 33
```

```python
m, s = 42, 2
c = public_key.encrypt(m)
c_prime = c * s
m_prime = private_key_ring.decrypt(c_prime)
# m_prime = 84 = 42 * 2
```
