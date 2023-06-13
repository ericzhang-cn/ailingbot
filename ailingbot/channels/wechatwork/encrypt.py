from __future__ import annotations

import base64
import hashlib
import socket
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def signature(
    *, token: str, timestamp: int, nonce: int, msg_encrypt: str
) -> str:
    """Calculates wechatwork message signature.

    :param token: Signature token.
    :type token: str
    :param timestamp: Signature timestamp.
    :type timestamp: int
    :param nonce: Signature nonce.
    :type nonce: int
    :param msg_encrypt: Signature content.
    :type msg_encrypt: str
    :return: The signature.
    :rtype: str
    """
    sort_list = [token, str(timestamp), str(nonce), msg_encrypt]
    sort_list.sort()
    sha = hashlib.sha1()
    sha.update(''.join(sort_list).encode())
    return sha.hexdigest()


def decrypt(*, key: str, msg_encrypt: str) -> tuple[str, str]:
    """Decrypts ciphertext.

    :param key: AES encrypt key.
    :type key: str
    :param msg_encrypt: Ciphertext.
    :type msg_encrypt: str
    :return: Message content and receiver id in plaintext.
    :rtype: typing.Tuple[str, str]
    """
    decoded_key = base64.b64decode(key + '=')
    cipher = Cipher(algorithms.AES(decoded_key), modes.CBC(decoded_key[:16]))
    decryptor = cipher.decryptor()
    plain_text = (
        decryptor.update(base64.b64decode(msg_encrypt)) + decryptor.finalize()
    )
    pad = plain_text[-1]
    content = plain_text[16:-pad]
    len_ = socket.ntohl(struct.unpack('I', content[:4])[0])
    return content[4 : len_ + 4].decode('utf-8'), content[len_ + 4 :].decode(
        'utf-8'
    )
