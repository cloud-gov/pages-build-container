import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)


def decrypt(ciphertext, key):
    m = hashlib.sha256()
    m.update(key.encode())
    hashed_key = m.digest()

    auth_tag, iv, encrypted = [
        bytes.fromhex(hex) for hex in ciphertext.split(':')
    ]

    decryptor = Cipher(
        algorithms.AES(hashed_key),
        modes.GCM(iv, auth_tag),
        backend=default_backend()
    ).decryptor()

    return (decryptor.update(encrypted) + decryptor.finalize()).decode()
