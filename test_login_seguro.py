import unittest
import sqlite3
import os
import time
from unittest.mock import patch, MagicMock
from login_seguro import LoginManager, login_seguro

class TestLoginManager(unittest.TestCase):
    
    def setUp(self):
        """Configurar base de datos de prueba"""
        self.test_db = "test_login.db"
        self.login_manager = LoginManager(self.test_db)
        
        # Crear tabla de usuarios de prueba
        with sqlite3.connect(self.test_db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT
                )
            ''')
            
            # Usuario de prueba
            test_password_hash = self.login_manager.hash_password("password123")
            cursor.execute(
                "INSERT OR REPLACE INTO users (username, password_hash) VALUES (?, ?)",
                ("testuser", test_password_hash)
            )
            conn.commit()
    
    def tearDown(self):
        """Limpiar después de cada test"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_login_exitoso(self):
        """Test login con credenciales correctas"""
        success, message = self.login_manager.login("testuser", "password123")
        self.assertTrue(success)
        self.assertIn("Bienvenido", message)
    
    def test_login_credenciales_incorrectas(self):
        """Test login con credenciales incorrectas"""
        success, message = self.login_manager.login("testuser", "wrongpassword")
        self.assertFalse(success)
        self.assertEqual(message, "Credenciales incorrectas")
    
    def test_login_usuario_inexistente(self):
        """Test login con usuario que no existe"""
        success, message = self.login_manager.login("noexiste", "password123")
        self.assertFalse(success)
        self.assertEqual(message, "Credenciales incorrectas")
    
    def test_login_credenciales_vacias(self):
        """Test login con credenciales vacías"""
        success, message = self.login_manager.login("", "")
        self.assertFalse(success)
        self.assertEqual(message, "Credenciales requeridas")
        
        success, message = self.login_manager.login("user", "")
        self.assertFalse(success)
        self.assertEqual(message, "Credenciales requeridas")
    
    def test_login_credenciales_muy_largas(self):
        """Test login con credenciales excesivamente largas"""
        long_username = "a" * 51
        long_password = "b" * 101
        
        success, message = self.login_manager.login(long_username, "password")
        self.assertFalse(success)
        self.assertEqual(message, "Credenciales inválidas")
        
        success, message = self.login_manager.login("user", long_password)
        self.assertFalse(success)
        self.assertEqual(message, "Credenciales inválidas")
    
    def test_sql_injection_prevention(self):
        """Test que previene ataques de SQL injection"""
        malicious_inputs = [
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "'; DELETE FROM users; --"
        ]
        
        for malicious_input in malicious_inputs:
            success, message = self.login_manager.login(malicious_input, "password")
            self.assertFalse(success)
            # Verificar que la tabla users aún existe
            with sqlite3.connect(self.test_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                self.assertIsNotNone(cursor.fetchone(), "Tabla users fue eliminada por SQL injection")
    
    def test_rate_limiting(self):
        """Test rate limiting después de múltiples intentos fallidos"""
        # Hacer 5 intentos fallidos
        for i in range(5):
            success, message = self.login_manager.login("testuser", "wrongpassword")
            self.assertFalse(success)
        
        # El 6to intento debe estar rate limited
        success, message = self.login_manager.login("testuser", "wrongpassword")
        self.assertFalse(success)
        self.assertIn("Demasiados intentos", message)
        
        # Incluso con credenciales correctas debe estar limitado
        success, message = self.login_manager.login("testuser", "password123")
        self.assertFalse(success)
        self.assertIn("Demasiados intentos", message)
    
    def test_rate_limiting_reset_after_success(self):
        """Test que rate limiting se resetea después de login exitoso"""
        # Hacer algunos intentos fallidos
        for i in range(3):
            self.login_manager.login("testuser", "wrongpassword")
        
        # Login exitoso debe resetear el contador
        success, message = self.login_manager.login("testuser", "password123")
        self.assertTrue(success)
        
        # Verificar que el usuario no está en failed_attempts
        self.assertNotIn("testuser", self.login_manager.failed_attempts)
    
    def test_hash_password_consistency(self):
        """Test que el hash de password es consistente"""
        password = "testpassword"
        hash1 = self.login_manager.hash_password(password)
        hash2 = self.login_manager.hash_password(password)
        self.assertEqual(hash1, hash2)
        
        # Diferentes passwords deben tener diferentes hashes
        hash3 = self.login_manager.hash_password("differentpassword")
        self.assertNotEqual(hash1, hash3)
    
    @patch('sqlite3.connect')
    def test_database_error_handling(self, mock_connect):
        """Test manejo de errores de base de datos"""
        mock_connect.side_effect = sqlite3.Error("Database error")
        
        success, message = self.login_manager.login("testuser", "password123")
        self.assertFalse(success)
        self.assertEqual(message, "Error del sistema")
    
    def test_login_seguro_function(self):
        """Test la función simplificada login_seguro"""
        # Crear BD para la función simplificada
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT
                )
            ''')
            
            # Hash de "password123"
            import hashlib
            salt = "mi_salt_secreto"
            password_hash = hashlib.sha256(("password123" + salt).encode()).hexdigest()
            
            cursor.execute(
                "INSERT OR REPLACE INTO users (username, password_hash) VALUES (?, ?)",
                ("admin", password_hash)
            )
            conn.commit()
        
        # Test función simplificada
        with patch('builtins.print'):  # Suprimir prints durante test
            result = login_seguro("admin", "password123")
            self.assertTrue(result)
            
            result = login_seguro("admin", "wrongpassword")
            self.assertFalse(result)
        
        # Limpiar
        if os.path.exists("users.db"):
            os.remove("users.db")

class TestSecurityFeatures(unittest.TestCase):
    """Tests específicos de características de seguridad"""
    
    def setUp(self):
        self.test_db = "security_test.db"
        self.login_manager = LoginManager(self.test_db)
    
    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_special_characters_in_credentials(self):
        """Test manejo de caracteres especiales"""
        special_chars = ["'", '"', ";", "--", "/*", "*/", "\\", "\n", "\r"]
        
        for char in special_chars:
            username = f"user{char}test"
            password = f"pass{char}word"
            
            # No debe causar errores de SQL
            success, message = self.login_manager.login(username, password)
            self.assertFalse(success)  # Usuario no existe, pero no debe haber error SQL
    
    def test_unicode_characters(self):
        """Test manejo de caracteres Unicode"""
        unicode_inputs = [
            ("用户", "密码"),  # Chino
            ("пользователь", "пароль"),  # Ruso
            ("usuario🔒", "contraseña💻"),  # Emojis
        ]
        
        for username, password in unicode_inputs:
            success, message = self.login_manager.login(username, password)
            self.assertFalse(success)  # No debe causar errores

if __name__ == '__main__':
    # Ejecutar tests con output detallado
    unittest.main(verbosity=2)