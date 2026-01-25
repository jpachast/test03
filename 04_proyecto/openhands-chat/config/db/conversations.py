"""
Database Conversations Mixin - Handles conversations and messages
"""
from typing import Optional, List, Dict


class ConversationsMixin:
    """Mixin para gestión de conversaciones y mensajes"""
    
    def create_conversation(self, project_id: int, title: str = None) -> int:
        """Crea una nueva conversación"""
        self._execute(
            """INSERT INTO conversations (project_id, title, created_at, updated_at)
               VALUES (?, ?, datetime('now'), datetime('now'))""",
            (project_id, title)
        )
        result = self._execute("SELECT last_insert_rowid()", fetch='one')
        return result[0] if result else 0
    
    def get_conversation(self, conv_id: int) -> Optional[Dict]:
        """Obtiene una conversación por ID"""
        result = self._execute(
            """SELECT id, project_id, title, created_at, updated_at
               FROM conversations WHERE id = ?""",
            (conv_id,),
            fetch='one'
        )
        if result:
            return {
                'id': result[0],
                'project_id': result[1],
                'title': result[2],
                'created_at': result[3],
                'updated_at': result[4]
            }
        return None
    
    def get_conversations(self, project_id: int = None, limit: int = 50) -> List[Dict]:
        """Obtiene conversaciones, opcionalmente filtradas por proyecto"""
        if project_id:
            results = self._execute(
                """SELECT id, project_id, title, created_at, updated_at
                   FROM conversations WHERE project_id = ?
                   ORDER BY updated_at DESC LIMIT ?""",
                (project_id, limit),
                fetch='all'
            )
        else:
            results = self._execute(
                """SELECT id, project_id, title, created_at, updated_at
                   FROM conversations ORDER BY updated_at DESC LIMIT ?""",
                (limit,),
                fetch='all'
            )
        
        conversations = []
        for row in results:
            conversations.append({
                'id': row[0],
                'project_id': row[1],
                'title': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            })
        return conversations
    
    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        """Agrega un mensaje a una conversación"""
        self._execute(
            """INSERT INTO messages (conversation_id, role, content, created_at)
               VALUES (?, ?, ?, datetime('now'))""",
            (conversation_id, role, content)
        )
        # Actualizar timestamp de conversación
        self._execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        result = self._execute("SELECT last_insert_rowid()", fetch='one')
        return result[0] if result else 0
    
    def get_messages(self, conversation_id: int) -> List[Dict]:
        """Obtiene mensajes de una conversación"""
        results = self._execute(
            """SELECT id, role, content, created_at
               FROM messages WHERE conversation_id = ?
               ORDER BY created_at ASC""",
            (conversation_id,),
            fetch='all'
        )
        messages = []
        for row in results:
            messages.append({
                'id': row[0],
                'role': row[1],
                'content': row[2],
                'created_at': row[3]
            })
        return messages
    
    def clear_messages(self, conversation_id: int):
        """Elimina todos los mensajes de una conversación"""
        self._execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
    
    def delete_conversation(self, conversation_id: int):
        """Elimina una conversación y sus mensajes"""
        self.clear_messages(conversation_id)
        self._execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
    
    def update_conversation_title(self, conversation_id: int, title: str):
        """Actualiza el título de una conversación"""
        self._execute(
            "UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, conversation_id)
        )
