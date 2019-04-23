import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from crypto_voting.crypto import keygen, Plaintext


class TestCrypto(unittest.TestCase):
    def test_encrypt_decrypt(self):
        public_key, private_key = keygen(n_bits=2048)
        plaintext = Plaintext(100)
        ciphertext = public_key.encrypt(plaintext)
        decrypted_plaintext = private_key.decrypt(ciphertext)

        self.assertNotEqual(plaintext.value, ciphertext.value)
        self.assertEqual(plaintext.value, decrypted_plaintext.value)


if __name__ == '__main__':
    unittest.main()
