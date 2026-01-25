"""
Database Projects Mixin - Handles project management
"""
from typing import Optional, List, Dict
from datetime import datetime


class ProjectsMixin:
    """Mixin para gestión de proyectos en la base de datos"""
    
    def add_project(self, name: str, path: str, git_url: str = None) -> int:
        """Agrega un nuevo proyecto"""
        self._execute(
            """INSERT INTO projects (name, path, git_url, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (name, path, git_url)
        )
        result = self._execute("SELECT last_insert_rowid()", fetch='one')
        return result[0] if result else 0
    
    def get_projects(self) -> List[Dict]:
        """Obtiene todos los proyectos"""
        results = self._execute(
            """SELECT id, name, path, git_url, created_at, updated_at
               FROM projects ORDER BY updated_at DESC""",
            fetch='all'
        )
        projects = []
        for row in results:
            projects.append({
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'git_url': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        return projects
    
    def update_project_access(self, project_id: int):
        """Actualiza la fecha de último acceso"""
        self._execute(
            "UPDATE projects SET updated_at = datetime('now') WHERE id = ?",
            (project_id,)
        )
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Obtiene un proyecto por ID"""
        result = self._execute(
            """SELECT id, name, path, git_url, created_at, updated_at
               FROM projects WHERE id = ?""",
            (project_id,),
            fetch='one'
        )
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'path': result[2],
                'git_url': result[3],
                'created_at': result[4],
                'updated_at': result[5]
            }
        return None
    
    def get_project_by_name(self, name: str) -> Optional[Dict]:
        """Obtiene un proyecto por nombre"""
        result = self._execute(
            """SELECT id, name, path, git_url, created_at, updated_at
               FROM projects WHERE name = ?""",
            (name,),
            fetch='one'
        )
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'path': result[2],
                'git_url': result[3],
                'created_at': result[4],
                'updated_at': result[5]
            }
        return None
    
    def delete_project(self, project_id: int):
        """Elimina un proyecto y sus conversaciones"""
        # Primero eliminar mensajes de conversaciones del proyecto
        self._execute(
            """DELETE FROM messages WHERE conversation_id IN
               (SELECT id FROM conversations WHERE project_id = ?)""",
            (project_id,)
        )
        # Eliminar conversaciones
        self._execute("DELETE FROM conversations WHERE project_id = ?", (project_id,))
        # Eliminar proyecto
        self._execute("DELETE FROM projects WHERE id = ?", (project_id,))
