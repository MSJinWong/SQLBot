"""
加密/解密工具 - 开源版本
使用本地 AES 加密实现，与前端保持一致
"""
from apps.datasource.utils.utils import aes_encrypt, aes_decrypt


async def sqlbot_decrypt(text: str) -> str:
    """解密 - 使用本地 AES 解密"""
    if not text:
        return text
    try:
        return aes_decrypt(text)
    except Exception:
        # 如果解密失败，返回原文（可能是未加密的数据）
        return text


async def sqlbot_encrypt(text: str) -> str:
    """加密 - 使用本地 AES 加密"""
    if not text:
        return text
    return aes_encrypt(text).decode('utf-8')