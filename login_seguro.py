import hashlib
import sqlite3
from typing import Optional, Tuple
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoginManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.failed_attempts = {}  # Rate limiting simple
        
    def hash_password(self, password: str) -> str:
        """Hashea la contraseña usando SHA-256 con salt"""
        salt = "mi_salt_secreto"  # En producción, usar salt único por usuario
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def is_rate_limited(self, username: str) -> bool:
        """Verifica si el usuario está limitado por intentos fallidos"""
        if username in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[username]
            if attempts >= 5 and time.time() - last_attempt < 300:  # 5 minutos
                return True
        return False
    
    def record_failed_attempt(self, username: str):
        """Registra intento fallido para rate limiting"""
        current_time = time.time()
        if username in self.failed_attempts:
            attempts, _ = self.failed_attempts[username]
            self.failed_attempts[username] = (attempts + 1, current_time)
        else:
            self.failed_attempts[username] = (1, current_time)
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Autentica un usuario de forma segura
        
        Args:
            username (str): Nombre de usuario
            password (str): Contraseña en texto plano
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
            
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        # Validación de inputs
        if not username or not password:
            logger.warning("Login attempt with empty credentials")
            return False, "Credenciales requeridas"
            
        if len(username) > 50 or len(password) > 100:
            logger.warning(f"Login attempt with oversized credentials: {username[:10]}...")
            return False, "Credenciales inválidas"
            
        # Rate limiting
        if self.is_rate_limited(username):
            logger.warning(f"Rate limited login attempt: {username}")
            return False, "Demasiados intentos fallidos. Intenta en 5 minutos"
        
        try:
            # Conexión segura a BD
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Query parametrizada (previene SQL injection)
                hashed_password = self.hash_password(password)
                cursor.execute(
                    "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
                    (username, hashed_password)
                )
                
                result = cursor.fetchone()
                
                if result:
                    user_id, username = result
                    logger.info(f"Successful login: {username}")
                    # Limpiar intentos fallidos
                    if username in self.failed_attempts:
                        del self.failed_attempts[username]
                    return True, f"Bienvenido {username}"
                else:
                    logger.warning(f"Failed login attempt: {username}")
                    self.record_failed_attempt(username)
                    return False, "Credenciales incorrectas"
                    
        except sqlite3.Error as e:
            logger.error(f"Database error during login: {e}")
            return False, "Error del sistema"
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            return False, "Error inesperado"

# Función simple compatible con tu código original
def login_seguro(username: str, password: str) -> bool:
    """
    Versión simplificada y segura de login
    
    Args:
        username: Nombre de usuario
        password: Contraseña
        
    Returns:
        bool: True si login exitoso, False si falla
    """
    login_manager = LoginManager("users.db")
    success, message = login_manager.login(username, password)
    print(message)  # Para debugging
    return success

if __name__ == "__main__":
    # Ejemplo de uso
    login_manager = LoginManager("test.db")
    
    # Test cases
    print(login_manager.login("", ""))  # Credenciales vacías
    print(login_manager.login("admin", "password123"))  # Login normal
    print(login_manager.login("admin'; DROP TABLE users; --", "hack"))  # SQL injection attempt