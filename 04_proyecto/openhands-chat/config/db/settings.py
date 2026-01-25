"""
Database Settings Mixin - Handles application settings storage
"""
from typing import Optional


class SettingsMixin:
    """Mixin para gestión de settings en la base de datos"""
    
    def set_setting(self, key: str, value: str, encrypt: bool = False):
        """Guarda una configuración"""
        if encrypt and hasattr(self, '_encrypt'):
            value = self._encrypt(value)
        self._execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Obtiene una configuración"""
        result = self._execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
            fetch='one'
        )
        if result:
            value = result[0]
            # Intentar descifrar si parece cifrado
            if hasattr(self, '_decrypt'):
                decrypted = self._decrypt(value)
                if decrypted:
                    return decrypted
            return value
        return default
    
    def get_all_settings(self) -> dict:
        """Obtiene todas las configuraciones"""
        results = self._execute("SELECT key, value FROM settings", fetch='all')
        settings = {}
        for key, value in results:
            if hasattr(self, '_decrypt'):
                decrypted = self._decrypt(value)
                if decrypted:
                    value = decrypted
            settings[key] = value
        return settings
    
    def delete_setting(self, key: str):
        """Elimina una configuración"""
        self._execute("DELETE FROM settings WHERE key = ?", (key,))
    
    def set_api_key(self, api_key: str):
        """Guarda la API key cifrada"""
        self.set_setting('api_key', api_key, encrypt=True)
    
    def get_api_key(self) -> Optional[str]:
        """Obtiene la API key descifrada"""
        return self.get_setting('api_key')
    
    def has_api_key(self) -> bool:
        """Verifica si hay API key configurada"""
        key = self.get_api_key()
        return bool(key and len(key) > 10)
    
    def set_github_token(self, token: str, force: bool = False):
        """Guarda el token de GitHub cifrado"""
        if force or not self.get_setting('github_token'):
            self.set_setting('github_token', token, encrypt=True)
    
    def get_github_token(self) -> Optional[str]:
        """Obtiene el token de GitHub descifrado"""
        return self.get_setting('github_token')
