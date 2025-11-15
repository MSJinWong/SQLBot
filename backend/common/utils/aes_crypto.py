from typing import Optional
from common.core.config import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

# 开发环境简化实现（生产环境需要 sqlbot_xpack）
simple_aes_iv_text = 'sqlbot_em_aes_iv'

def sqlbot_aes_encrypt(text: str, key: Optional[str] = None) -> str:
    """简化的 AES 加密实现"""
    return simple_aes_encrypt(text, key)

def sqlbot_aes_decrypt(text: str, key: Optional[str] = None) -> str:
    """简化的 AES 解密实现"""
    return simple_aes_decrypt(text, key)

def simple_aes_encrypt(text: str, key: Optional[str] = None, ivtext: Optional[str] = None) -> str:
    """AES CBC 加密"""
    key_bytes = (key or settings.SECRET_KEY)[:32].encode('utf-8')
    key_bytes = key_bytes.ljust(32, b'\0')[:32]
    iv_bytes = (ivtext or simple_aes_iv_text).encode('utf-8')
    iv_bytes = iv_bytes.ljust(16, b'\0')[:16]

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    encrypted = cipher.encrypt(pad(text.encode('utf-8'), AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')

def simple_aes_decrypt(text: str, key: Optional[str] = None, ivtext: Optional[str] = None) -> str:
    """AES CBC 解密"""
    key_bytes = (key or settings.SECRET_KEY)[:32].encode('utf-8')
    key_bytes = key_bytes.ljust(32, b'\0')[:32]
    iv_bytes = (ivtext or simple_aes_iv_text).encode('utf-8')
    iv_bytes = iv_bytes.ljust(16, b'\0')[:16]

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    decrypted = unpad(cipher.decrypt(base64.b64decode(text)), AES.block_size)
    return decrypted.decode('utf-8')