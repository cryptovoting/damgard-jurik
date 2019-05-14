# Damgard-Jurik

An implementation of the [Damgard-Jurik](https://people.csail.mit.edu/rivest/voting/papers/DamgardJurikNielsen-AGeneralizationOfPailliersPublicKeySystemWithApplicationsToElectronicVoting.pdf) multi-authority, homomorphic encryption cryptosystem.

## Table of Contents

* [Installation](#installation)
* [Public and Private Keys](#public-and-private-keys)
* [Key Generation](#key-generation)
* [Encryption and Decryption](#encryption-and-decryption)
* [Homomorphic Operations](#homomorphic-operations)

## Installation

Requires Python 3.6+.

```bash
git clone https://github.com/cryptovoting/damgard-jurik.git
cd damgard-jurik
pip install -e damgard_jurik
```
*Note that the `-e` flag will instruct pip to install the package as "editable". That is, when changes are made to any part of the package during development, those changes will immediately be available system-wide on the activated python environment.*

All requirements for this package should be added to `setup.py`.

## Public and Private Keys

In the multi-authority variant of Damgard-Jurik implemented in this repository, a key pair consists of single public key along with a private key that has been split into multiple components using [Shamir's secret sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing). The public key encrypts messages while the shares of the private key all contribute a portion of the decryption without ever requiring reconstruction of the private key. Thus, trust is distributed among the holders of the private key shares.

In this implementation, the public key is a `PublicKey` object with an encrypt function while the private key shares are `PrivateKeyShare` objects with a decrypt function that performs a partial decryption using that share of the private key. A `PrivateKeyRing` object holds a set of `PrivateKeyShare`s and contains a decrypt function that calls each `PrivateKeyShare`'s decrypt function and combines the results to obtain the final decryption.

## Key Generation

To generate a `PublicKey` and corresponding `PrivateKeyRing`, run the following commands:

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
- `s`: The exponent to which the public key parameter `n` is raised (where `n = p * q` is the product of two `n_bits`-bit primes `p` and `q`.). Plaintexts live in the space `Z_n^s`.
- `threshold`: The minimum number of private key shares needed to decrypt an encrypted message.
- `n_shares`: The number of private key shares to generate.


## Encryption and Decryption

To encrypt an integer `m`, run `public_key.encrypt(m)`. This will return an `EncryptedNumber` containing the encryption of `m`.

To decrypt an `EncryptedNumber` `c`, run `private_key_ring.decrypt(c)`. This will return an integer containing the decryption of `c`.

For example:

```python
m = 42
c = public_key.encrypt(m)
m_prime = private_key_ring.decrypt(c)
# m_prime = 42
```

Additionally, `PublicKey`s and `PrivateKingRing`s have a convenience method for encrypting and decrypting lists of integers, as shown below.

```python
m_list = [42, 33, 100]
c_list = public_key.encrypt(m_list)
m_prime_list = private_key_ring.decrypt(c_list)
# m_prime_list = [42, 33, 100]
```

## Homomorphic Operations

Due to the additively homomorphic nature of the Damgard-Jurik cryptosystem, encrypted numbers can be combined in such a way as to obtain an encryption of the sum of the associated plaintexts. Futhermore, encrypted numbers can be combined with un-encrypted integers in such a way as to obtain the product of the associated plaintext and the un-encrypted integer. For convenience, the `+`, `-`, `*`, and `/` operators have been overridden for `EncryptedNumbers` to implement these combinations.

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
