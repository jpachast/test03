"""
Checkpoints - Sistema real de snapshots del código

Características:
- Snapshots reales del estado del proyecto
- Restore a versiones anteriores como Git
- Almacenamiento de estados en DB
- Diff entre checkpoints
"""

import os
import json
import hashlib
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import difflib

logger = logging.getLogger(__name__)


@dataclass
class FileSnapshot:
    """Snapshot de un archivo"""
    path: str
    content: str
    hash: str
    size: int
    modified_at: str
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "hash": self.hash,
            "size": self.size,
            "modified_at": self.modified_at,
            "content_preview": self.content[:200] + "..." if len(self.content) > 200 else self.content
        }


@dataclass
class Checkpoint:
    """Un checkpoint/snapshot del proyecto"""
    id: str
    name: str
    description: str
    created_at: datetime
    workspace: str
    files: Dict[str, FileSnapshot] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "workspace": self.workspace,
            "file_count": len(self.files),
            "total_size": sum(f.size for f in self.files.values()),
            "files": [f.to_dict() for f in list(self.files.values())[:20]],  # Limitar preview
            "metadata": self.metadata
        }


class CheckpointManager:
    """
    Gestor de Checkpoints - Sistema de snapshots del código
    
    Funcionalidades:
    - Crear snapshots del estado actual
    - Restaurar a checkpoints anteriores
    - Ver diff entre checkpoints
    - Listar historial de checkpoints
    """
    
    IGNORE_DIRS = {
        'node_modules', '__pycache__', '.git', '.venv', 'venv',
        'env', '.env', 'dist', 'build', '.next', 'coverage',
        '.pytest_cache', '.mypy_cache', 'eggs', '*.egg-info'
    }
    
    IGNORE_FILES = {
        '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.so',
        '*.dylib', '*.dll', '*.exe', '*.bin'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css',
        '.json', '.yaml', '.yml', '.md', '.txt', '.sh', '.sql',
        '.env.example', '.gitignore', '.dockerignore', 'Dockerfile',
        '.toml', '.ini', '.cfg', '.conf'
    }
    
    def __init__(self, max_checkpoints: int = 50):
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._checkpoint_order: List[str] = []  # Orden cronológico
        self.max_checkpoints = max_checkpoints
    
    def _generate_id(self) -> str:
        """Genera ID único para checkpoint"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"cp_{timestamp}_{random_suffix}"
    
    def _hash_content(self, content: str) -> str:
        """Genera hash del contenido"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _should_include_file(self, file_path: str) -> bool:
        """Verifica si un archivo debe incluirse en el snapshot"""
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        # Verificar extensiones soportadas o archivos especiales
        if ext in self.SUPPORTED_EXTENSIONS or filename in self.SUPPORTED_EXTENSIONS:
            return True
        
        # Verificar patrones de archivos ignorados
        for pattern in self.IGNORE_FILES:
            if pattern.startswith('*'):
                if filename.endswith(pattern[1:]):
                    return False
            elif filename == pattern:
                return False
        
        return ext in self.SUPPORTED_EXTENSIONS
    
    def create_checkpoint(
        self,
        workspace: str,
        name: str,
        description: str = "",
        max_files: int = 100,
        max_file_size: int = 100000  # 100KB por archivo
    ) -> Checkpoint:
        """
        Crea un checkpoint del estado actual del workspace.
        
        Args:
            workspace: Ruta del directorio a capturar
            name: Nombre del checkpoint
            description: Descripción opcional
            max_files: Máximo de archivos a incluir
            max_file_size: Tamaño máximo por archivo en bytes
        
        Returns:
            Checkpoint creado
        """
        workspace = Path(workspace)
        if not workspace.exists():
            raise ValueError(f"Workspace no existe: {workspace}")
        
        checkpoint_id = self._generate_id()
        files: Dict[str, FileSnapshot] = {}
        files_processed = 0
        
        for root, dirs, filenames in os.walk(workspace):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            for filename in filenames:
                if files_processed >= max_files:
                    break
                
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, workspace)
                
                if not self._should_include_file(file_path):
                    continue
                
                try:
                    # Verificar tamaño
                    file_size = os.path.getsize(file_path)
                    if file_size > max_file_size:
                        continue
                    
                    # Leer contenido
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Crear snapshot del archivo
                    file_snapshot = FileSnapshot(
                        path=rel_path,
                        content=content,
                        hash=self._hash_content(content),
                        size=file_size,
                        modified_at=datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).isoformat()
                    )
                    
                    files[rel_path] = file_snapshot
                    files_processed += 1
                    
                except Exception as e:
                    logger.warning(f"Error leyendo {file_path}: {e}")
            
            if files_processed >= max_files:
                break
        
        # Crear checkpoint
        checkpoint = Checkpoint(
            id=checkpoint_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            workspace=str(workspace),
            files=files,
            metadata={
                "files_count": len(files),
                "total_size": sum(f.size for f in files.values())
            }
        )
        
        # Almacenar
        self._checkpoints[checkpoint_id] = checkpoint
        self._checkpoint_order.append(checkpoint_id)
        
        # Limpiar checkpoints antiguos si excede el límite
        while len(self._checkpoint_order) > self.max_checkpoints:
            old_id = self._checkpoint_order.pop(0)
            del self._checkpoints[old_id]
        
        logger.info(f"[Checkpoint] Creado: {checkpoint_id} con {len(files)} archivos")
        
        return checkpoint
    
    def restore_checkpoint(
        self,
        checkpoint_id: str,
        target_workspace: str = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Restaura un checkpoint al workspace.
        
        Args:
            checkpoint_id: ID del checkpoint a restaurar
            target_workspace: Directorio destino (opcional, usa el original)
            dry_run: Si True, solo muestra qué se haría sin ejecutar
        
        Returns:
            Resultado de la restauración
        """
        if checkpoint_id not in self._checkpoints:
            raise ValueError(f"Checkpoint no encontrado: {checkpoint_id}")
        
        checkpoint = self._checkpoints[checkpoint_id]
        workspace = Path(target_workspace or checkpoint.workspace)
        
        result = {
            "checkpoint_id": checkpoint_id,
            "checkpoint_name": checkpoint.name,
            "workspace": str(workspace),
            "dry_run": dry_run,
            "files_restored": [],
            "files_created": [],
            "files_modified": [],
            "errors": []
        }
        
        for rel_path, file_snapshot in checkpoint.files.items():
            file_path = workspace / rel_path
            
            try:
                exists = file_path.exists()
                current_hash = None
                
                if exists:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        current_hash = self._hash_content(f.read())
                
                # Determinar acción
                if not exists:
                    action = "create"
                    result["files_created"].append(rel_path)
                elif current_hash != file_snapshot.hash:
                    action = "modify"
                    result["files_modified"].append(rel_path)
                else:
                    action = "skip"  # Sin cambios
                    continue
                
                if not dry_run and action in ["create", "modify"]:
                    # Crear directorio si no existe
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Escribir contenido
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_snapshot.content)
                    
                    result["files_restored"].append(rel_path)
                    
            except Exception as e:
                result["errors"].append({"file": rel_path, "error": str(e)})
        
        result["success"] = len(result["errors"]) == 0
        result["total_restored"] = len(result["files_restored"])
        
        return result
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Obtiene un checkpoint por ID"""
        return self._checkpoints.get(checkpoint_id)
    
    def list_checkpoints(self, limit: int = 20) -> List[Dict]:
        """Lista todos los checkpoints (más recientes primero)"""
        checkpoints = []
        
        for cp_id in reversed(self._checkpoint_order[-limit:]):
            cp = self._checkpoints.get(cp_id)
            if cp:
                checkpoints.append({
                    "id": cp.id,
                    "name": cp.name,
                    "description": cp.description,
                    "created_at": cp.created_at.isoformat(),
                    "file_count": len(cp.files),
                    "total_size": sum(f.size for f in cp.files.values())
                })
        
        return checkpoints
    
    def diff_checkpoints(
        self,
        checkpoint_id_1: str,
        checkpoint_id_2: str
    ) -> Dict[str, Any]:
        """
        Compara dos checkpoints y muestra las diferencias.
        
        Returns:
            Diff entre los dos checkpoints
        """
        cp1 = self._checkpoints.get(checkpoint_id_1)
        cp2 = self._checkpoints.get(checkpoint_id_2)
        
        if not cp1 or not cp2:
            raise ValueError("Uno o ambos checkpoints no encontrados")
        
        files1 = set(cp1.files.keys())
        files2 = set(cp2.files.keys())
        
        result = {
            "checkpoint_1": {"id": cp1.id, "name": cp1.name},
            "checkpoint_2": {"id": cp2.id, "name": cp2.name},
            "added": list(files2 - files1),
            "removed": list(files1 - files2),
            "modified": [],
            "unchanged": []
        }
        
        # Comparar archivos comunes
        common_files = files1 & files2
        for file_path in common_files:
            f1 = cp1.files[file_path]
            f2 = cp2.files[file_path]
            
            if f1.hash != f2.hash:
                # Generar diff
                diff = list(difflib.unified_diff(
                    f1.content.splitlines(keepends=True),
                    f2.content.splitlines(keepends=True),
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}",
                    lineterm=""
                ))
                
                result["modified"].append({
                    "path": file_path,
                    "diff_lines": len(diff),
                    "diff_preview": "".join(diff[:50])  # Primeras 50 líneas
                })
            else:
                result["unchanged"].append(file_path)
        
        result["summary"] = {
            "added": len(result["added"]),
            "removed": len(result["removed"]),
            "modified": len(result["modified"]),
            "unchanged": len(result["unchanged"])
        }
        
        return result
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Elimina un checkpoint"""
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            if checkpoint_id in self._checkpoint_order:
                self._checkpoint_order.remove(checkpoint_id)
            return True
        return False
    
    def get_file_content(self, checkpoint_id: str, file_path: str) -> Optional[str]:
        """Obtiene el contenido de un archivo en un checkpoint"""
        cp = self._checkpoints.get(checkpoint_id)
        if cp and file_path in cp.files:
            return cp.files[file_path].content
        return None
    
    def get_stats(self) -> Dict:
        """Estadísticas del sistema de checkpoints"""
        total_files = sum(len(cp.files) for cp in self._checkpoints.values())
        total_size = sum(
            sum(f.size for f in cp.files.values())
            for cp in self._checkpoints.values()
        )
        
        return {
            "total_checkpoints": len(self._checkpoints),
            "total_files_stored": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_checkpoints": self.max_checkpoints
        }


# Instancia global
_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Obtiene o crea el gestor de checkpoints"""
    global _manager
    if _manager is None:
        _manager = CheckpointManager()
    return _manager
