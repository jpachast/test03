"""
Base de datos SQLite para configuración
"""

import os
import sqlite3
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "config.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._cipher = self._get_cipher()
    
    def _get_cipher(self) -> Fernet:
        """Obtener cipher para encriptar/desencriptar"""
        # Usar una key derivada del hostname (simple pero efectivo para uso local)
        salt = b'openhands-chat-salt'
        password = (os.environ.get('ENCRYPTION_KEY', 'default-key') + 
                   str(self.db_path)).encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def _init_db(self):
        """Inicializar tablas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de configuración
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                encrypted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de proyectos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                git_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de conversaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _encrypt(self, value: str) -> str:
        """Encriptar valor"""
        return self._cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, value: str) -> str:
        """Desencriptar valor"""
        try:
            return self._cipher.decrypt(value.encode()).decode()
        except:
            return value
    
    # === SETTINGS ===
    
    def set_setting(self, key: str, value: str, encrypt: bool = False):
        """Guardar configuración"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stored_value = self._encrypt(value) if encrypt else value
        
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, encrypted, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (key, stored_value, 1 if encrypt else 0))
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key: str, default: str = None) -> str:
        """Obtener configuración"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value, encrypted FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return default
        
        value, encrypted = row
        return self._decrypt(value) if encrypted else value
    
    def get_all_settings(self) -> dict:
        """Obtener todas las configuraciones (sin desencriptar las sensibles)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value, encrypted FROM settings')
        rows = cursor.fetchall()
        conn.close()
        
        settings = {}
        for key, value, encrypted in rows:
            if encrypted:
                settings[key] = "********"  # No mostrar valores encriptados
            else:
                settings[key] = value
        
        return settings
    
    def delete_setting(self, key: str):
        """Eliminar configuración"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM settings WHERE key = ?', (key,))
        conn.commit()
        conn.close()
    
    # === API KEY (métodos específicos) ===
    
    def set_api_key(self, api_key: str):
        """Guardar API key encriptada"""
        self.set_setting('llm_api_key', api_key, encrypt=True)
    
    def get_api_key(self) -> str:
        """Obtener API key"""
        return self.get_setting('llm_api_key', '')
    
    def has_api_key(self) -> bool:
        """Verificar si hay API key configurada"""
        key = self.get_api_key()
        return key is not None and len(key) > 0
    
    # === PROYECTOS ===
    
    def add_project(self, name: str, path: str, git_url: str = None) -> int:
        """Agregar proyecto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projects (name, path, git_url)
            VALUES (?, ?, ?)
        ''', (name, path, git_url))
        
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return project_id
    
    def get_projects(self) -> list:
        """Obtener todos los proyectos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, path, git_url, created_at, last_accessed
            FROM projects
            ORDER BY last_accessed DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'git_url': row[3],
                'created_at': row[4],
                'last_accessed': row[5]
            }
            for row in rows
        ]
    
    def update_project_access(self, project_id: int):
        """Actualizar última vez accedido"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE projects SET last_accessed = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (project_id,))
        conn.commit()
        conn.close()
