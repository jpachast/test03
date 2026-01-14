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
    
    def _get_cipher(self, use_legacy: bool = False) -> Fernet:
        """Obtener cipher para encriptar/desencriptar
        
        Args:
            use_legacy: Si True, usa el cifrado antiguo para intentar desencriptar tokens viejos
        """
        if use_legacy:
            # Cifrado ANTIGUO (antes de v2)
            salt = b'openhands-chat-salt'
            password = (os.environ.get('ENCRYPTION_KEY', 'default-key') + str(self.db_path)).encode()
        else:
            # Cifrado NUEVO (v2) - usar por defecto
            salt = b'openhands-chat-salt-v2'
            password = b'openhands-chat-fixed-encryption-key-2024'
        
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
        
        # Tabla de proyectos/repositorios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                git_url TEXT,
                repo_owner TEXT,
                repo_name TEXT,
                branch TEXT DEFAULT 'main',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de conversaciones (mejorada)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Tabla de mensajes del chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        # Migrar tablas existentes si es necesario
        self._migrate_tables(cursor)
        
        conn.commit()
        conn.close()
    
    def _migrate_tables(self, cursor):
        """Migrar tablas existentes - NUNCA borrar datos"""
        # Obtener columnas existentes de cada tabla
        def get_columns(table):
            cursor.execute(f"PRAGMA table_info({table})")
            return [row[1] for row in cursor.fetchall()]
        
        # Migrar projects
        project_cols = get_columns('projects')
        if 'repo_owner' not in project_cols:
            cursor.execute('ALTER TABLE projects ADD COLUMN repo_owner TEXT')
        if 'repo_name' not in project_cols:
            cursor.execute('ALTER TABLE projects ADD COLUMN repo_name TEXT')
        if 'branch' not in project_cols:
            cursor.execute('ALTER TABLE projects ADD COLUMN branch TEXT DEFAULT "main"')
        
        # Migrar conversations
        conv_cols = get_columns('conversations')
        if 'status' not in conv_cols:
            cursor.execute('ALTER TABLE conversations ADD COLUMN status TEXT DEFAULT "active"')
        if 'updated_at' not in conv_cols:
            cursor.execute('ALTER TABLE conversations ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def _encrypt(self, value: str) -> str:
        """Encriptar valor con cifrado nuevo (v2)"""
        return self._cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, value: str) -> str:
        """Desencriptar valor - intenta con cifrado nuevo y luego legacy"""
        # Primero intentar con el cifrado nuevo (v2)
        try:
            return self._cipher.decrypt(value.encode()).decode()
        except Exception:
            pass
        
        # Si falla, intentar con el cifrado legacy
        try:
            legacy_cipher = self._get_cipher(use_legacy=True)
            decrypted = legacy_cipher.decrypt(value.encode()).decode()
            # Si funciona, re-encriptar con el nuevo cifrado para migrar
            self._migrate_encrypted_value(value, decrypted)
            return decrypted
        except Exception:
            pass
        
        # Si todo falla, devolver el valor tal cual (puede no estar encriptado)
        return value
    
    def _migrate_encrypted_value(self, old_encrypted: str, decrypted_value: str):
        """Migrar un valor del cifrado legacy al nuevo (se hace en set_setting)"""
        # La migración real se hace cuando se guarda de nuevo el valor
        pass
    
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

    def get_project(self, project_id: int) -> dict:
        """Obtener proyecto por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, path, git_url, repo_owner, repo_name, branch
            FROM projects WHERE id = ?
        ''', (project_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'git_url': row[3],
                'repo_owner': row[4],
                'repo_name': row[5],
                'branch': row[6]
            }
        return None

    def get_project_by_name(self, name: str) -> dict:
        """Obtener proyecto por nombre"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, path FROM projects WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'id': row[0], 'name': row[1], 'path': row[2]}
        return None

    # === CONVERSACIONES ===

    def create_conversation(self, project_id: int, title: str = None) -> int:
        """Crear nueva conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (project_id, title)
            VALUES (?, ?)
        ''', (project_id, title or "Nueva conversación"))
        conv_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conv_id

    def get_conversation(self, conv_id_or_project_id: int, by_conv_id: bool = False) -> dict:
        """Obtener conversación con info del proyecto
        
        Args:
            conv_id_or_project_id: ID de conversación o proyecto según by_conv_id
            by_conv_id: Si True, busca por conversation_id, si False por project_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if by_conv_id:
            # Buscar por ID de conversación
            cursor.execute('''
                SELECT c.id, c.title, c.created_at, c.project_id,
                       p.name, p.path, p.repo_owner, p.repo_name, p.branch
                FROM conversations c
                LEFT JOIN projects p ON c.project_id = p.id
                WHERE c.id = ?
            ''', (conv_id_or_project_id,))
        else:
            # Buscar por project_id (comportamiento anterior)
            cursor.execute('''
                SELECT c.id, c.title, c.created_at, c.project_id,
                       p.name, p.path, p.repo_owner, p.repo_name, p.branch
                FROM conversations c
                LEFT JOIN projects p ON c.project_id = p.id
                WHERE c.project_id = ?
                ORDER BY c.created_at DESC LIMIT 1
            ''', (conv_id_or_project_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'created_at': row[2],
                'project_id': row[3],
                'project_name': row[4],
                'workspace_path': row[5],  # path del proyecto
                'repo_owner': row[6],
                'repo_name': row[7],
                'branch': row[8]
            }
        
        # Si busca por project_id y no existe, crear
        if not by_conv_id:
            conv_id = self.create_conversation(conv_id_or_project_id)
            return {'id': conv_id, 'title': 'Nueva conversación', 'created_at': None}
        
        return None

    # === MENSAJES ===

    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        """Agregar mensaje a la conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        ''', (conversation_id, role, content))
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return msg_id

    def get_messages(self, conversation_id: int) -> list:
        """Obtener mensajes de una conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, role, content, created_at FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        ''', (conversation_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {'id': row[0], 'role': row[1], 'content': row[2], 'created_at': row[3]}
            for row in rows
        ]

    def get_messages_by_project(self, project_name: str) -> list:
        """Obtener mensajes de un proyecto por nombre"""
        project = self.get_project_by_name(project_name)
        if not project:
            return []
        conv = self.get_conversation(project['id'])
        return self.get_messages(conv['id'])

    def delete_conversation(self, conversation_id: int):
        """Eliminar conversación y sus mensajes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
        cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        conn.commit()
        conn.close()

    def delete_project(self, project_id: int):
        """Eliminar proyecto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit()
        conn.close()

    # === GITHUB ===
    
    def set_github_token(self, token: str, force: bool = False):
        """Guardar GitHub token encriptado
        
        PROTECCIÓN: No sobrescribe un token PAT (ghp_) con un token de GitHub App (ghu_)
        a menos que force=True
        """
        # Verificar si ya hay un token PAT válido
        if not force:
            existing_token = self.get_github_token()
            if existing_token and existing_token.startswith('ghp_'):
                # Ya hay un PAT, verificar qué tipo de token se quiere guardar
                if token.startswith('ghu_'):
                    # NO sobrescribir PAT con GitHub App token
                    print(f"⚠️  PROTECCIÓN: No se sobrescribe token PAT existente con token de GitHub App")
                    return False
        
        self.set_setting('github_token', token, encrypt=True)
        return True
    
    def get_github_token(self) -> str:
        """Obtener GitHub token"""
        return self.get_setting('github_token', '')
    
    def has_github_token(self) -> bool:
        """Verificar si hay GitHub token configurado"""
        token = self.get_github_token()
        return token is not None and len(token) > 0
    
    def get_github_token_type(self) -> str:
        """Obtener el tipo de token de GitHub
        Returns: 'pat' (Personal Access Token), 'app' (GitHub App), o 'unknown'
        """
        token = self.get_github_token()
        if not token:
            return 'none'
        if token.startswith('ghp_'):
            return 'pat'
        if token.startswith('ghu_'):
            return 'app'
        return 'unknown'
    
    def set_github_username(self, username: str):
        """Guardar GitHub username"""
        self.set_setting('github_username', username)
    
    def get_github_username(self) -> str:
        """Obtener GitHub username"""
        return self.get_setting('github_username', '')

    # === PROYECTOS CON REPO ===
    
    def add_project_with_repo(self, name: str, path: str, repo_owner: str, 
                               repo_name: str, branch: str = 'main', 
                               git_url: str = None) -> int:
        """Agregar proyecto con información de repositorio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projects (name, path, git_url, repo_owner, repo_name, branch)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, path, git_url, repo_owner, repo_name, branch))
        
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return project_id
    
    def get_project_by_repo(self, repo_owner: str, repo_name: str, branch: str) -> dict:
        """Obtener proyecto por repo y branch"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, path, git_url, repo_owner, repo_name, branch
            FROM projects 
            WHERE repo_owner = ? AND repo_name = ? AND branch = ?
        ''', (repo_owner, repo_name, branch))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0], 'name': row[1], 'path': row[2],
                'git_url': row[3], 'repo_owner': row[4],
                'repo_name': row[5], 'branch': row[6]
            }
        return None

    # === CONVERSACIONES MEJORADAS ===
    
    def get_all_conversations(self, limit: int = 50) -> list:
        """Obtener todas las conversaciones recientes con info del proyecto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.title, c.status, c.created_at, c.updated_at,
                   p.id as project_id, p.name as project_name, 
                   p.repo_owner, p.repo_name, p.branch
            FROM conversations c
            LEFT JOIN projects p ON c.project_id = p.id
            ORDER BY c.updated_at DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'title': row[1],
                'status': row[2],
                'created_at': row[3],
                'updated_at': row[4],
                'project_id': row[5],
                'project_name': row[6],
                'repo_owner': row[7],
                'repo_name': row[8],
                'branch': row[9]
            }
            for row in rows
        ]
    
    def update_conversation(self, conversation_id: int, title: str = None, status: str = None):
        """Actualizar conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = ['updated_at = CURRENT_TIMESTAMP']
        params = []
        
        if title:
            updates.append('title = ?')
            params.append(title)
        if status:
            updates.append('status = ?')
            params.append(status)
        
        params.append(conversation_id)
        
        cursor.execute(f'''
            UPDATE conversations SET {', '.join(updates)}
            WHERE id = ?
        ''', params)
        
        conn.commit()
        conn.close()
    
    def get_conversations_by_project(self, project_id: int) -> list:
        """Obtener conversaciones de un proyecto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, status, created_at, updated_at
            FROM conversations
            WHERE project_id = ?
            ORDER BY updated_at DESC
        ''', (project_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0], 'title': row[1], 'status': row[2],
                'created_at': row[3], 'updated_at': row[4]
            }
            for row in rows
        ]
