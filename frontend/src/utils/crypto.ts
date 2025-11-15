/**
 * 加密/解密工具 - 开源版本
 * 使用本地 AES 加密实现，与后端保持一致
 */
import CryptoJS from 'crypto-js'

const key = CryptoJS.enc.Utf8.parse('SQLBot1234567890')

/**
 * AES 加密
 * @param str 要加密的字符串
 * @returns 加密后的字符串
 */
export const encrypt = (str: string): string => {
  if (!str) return str
  return CryptoJS.AES.encrypt(str, key, {
    mode: CryptoJS.mode.ECB,
    padding: CryptoJS.pad.Pkcs7,
  }).toString()
}

/**
 * AES 解密
 * @param str 要解密的字符串
 * @returns 解密后的字符串
 */
export const decrypt = (str: string): string => {
  if (!str) return str
  try {
    const bytes = CryptoJS.AES.decrypt(str, key, {
      mode: CryptoJS.mode.ECB,
      padding: CryptoJS.pad.Pkcs7,
    })
    return bytes.toString(CryptoJS.enc.Utf8)
  } catch (error) {
    // 如果解密失败，返回原文（可能是未加密的数据）
    console.warn('Decryption failed, returning original text:', error)
    return str
  }
}

