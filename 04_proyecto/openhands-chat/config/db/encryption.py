"""
Database Encryption - Handles encryption/decryption of sensitive data
"""
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet

# Cache de ciphers
_cipher_cache = {}


def _get_encryption_key(use_legacy: bool = False) -> bytes:
    """Obtiene o genera la clave de cifrado"""
    key_file = os.path.join(os.path.dirname(__file__), '..', '..', '.encryption_key')
    
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        # Generar nueva clave
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        return key


def get_cipher(use_legacy: bool = False) -> Fernet:
    """Obtiene un cipher Fernet para cifrado/descifrado"""
    cache_key = 'legacy' if use_legacy else 'current'
    
    if cache_key not in _cipher_cache:
        key = _get_encryption_key(use_legacy)
        _cipher_cache[cache_key] = Fernet(key)
    
    return _cipher_cache[cache_key]


def encrypt_value(value: str) -> str:
    """Cifra un valor string"""
    if not value:
        return ""
    cipher = get_cipher()
    encrypted = cipher.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_value(encrypted_value: str) -> Optional[str]:
    """Descifra un valor string"""
    if not encrypted_value:
        return None
    
    try:
        cipher = get_cipher()
        decoded = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = cipher.decrypt(decoded)
        return decrypted.decode()
    except Exception:
        # Intentar con cipher legacy
        try:
            cipher = get_cipher(use_legacy=True)
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return None


def is_encrypted(value: str) -> bool:
    """Verifica si un valor parece estar cifrado"""
    if not value:
        return False
    try:
        decoded = base64.urlsafe_b64decode(value.encode())
        return len(decoded) > 32  # Fernet tokens son > 32 bytes
    except Exception:
        return False
