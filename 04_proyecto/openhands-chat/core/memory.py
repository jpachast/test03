"""
RAG Memory System - Memoria persistente para el agente usando ChromaDB

Guarda y recupera contexto relevante del historial de conversaciones.
Funciona con búsqueda semántica para encontrar información relacionada.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Lazy imports para no bloquear si no está instalado
_chromadb = None
_collection = None
_embedding_function = None

def _get_chroma():
    """Inicializa ChromaDB de forma lazy"""
    global _chromadb, _collection, _embedding_function
    
    if _collection is not None:
        return _collection
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Directorio para persistir la memoria
        data_dir = Path(__file__).parent.parent / "data" / "memory"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cliente persistente
        _chromadb = chromadb.PersistentClient(
            path=str(data_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Usar embedding function por defecto de Chroma (all-MiniLM-L6-v2)
        _collection = _chromadb.get_or_create_collection(
            name="agent_memory",
            metadata={"description": "Agent conversation and action memory"}
        )
        
        print(f"[MEMORY] ChromaDB initialized with {_collection.count()} memories")
        return _collection
        
    except ImportError as e:
        print(f"[MEMORY] ChromaDB not available: {e}")
        return None
    except Exception as e:
        print(f"[MEMORY] Error initializing ChromaDB: {e}")
        return None


def _generate_id(content: str, timestamp: str) -> str:
    """Genera un ID único basado en contenido y timestamp"""
    return hashlib.md5(f"{content}:{timestamp}".encode()).hexdigest()[:16]


def save_memory(
    content: str,
    memory_type: str = "action",
    metadata: Optional[Dict] = None,
    conversation_id: Optional[int] = None,
    project: Optional[str] = None
) -> bool:
    """
    Guarda un recuerdo en la memoria del agente.
    
    Args:
        content: El contenido a recordar (descripción del cambio, archivo, etc.)
        memory_type: Tipo de memoria (action, file_change, command, response)
        metadata: Metadata adicional
        conversation_id: ID de la conversación
        project: Nombre del proyecto
    
    Returns:
        True si se guardó correctamente
    """
    collection = _get_chroma()
    if collection is None:
        return False
    
    try:
        timestamp = datetime.now().isoformat()
        doc_id = _generate_id(content, timestamp)
        
        # Preparar metadata
        doc_metadata = {
            "type": memory_type,
            "timestamp": timestamp,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        
        if conversation_id:
            doc_metadata["conversation_id"] = str(conversation_id)
        if project:
            doc_metadata["project"] = project
        if metadata:
            # Convertir valores a strings para ChromaDB
            for k, v in metadata.items():
                if isinstance(v, (list, dict)):
                    doc_metadata[k] = json.dumps(v)
                else:
                    doc_metadata[k] = str(v)
        
        # Guardar en ChromaDB
        collection.add(
            documents=[content],
            metadatas=[doc_metadata],
            ids=[doc_id]
        )
        
        print(f"[MEMORY] Saved: {memory_type} - {content[:50]}...")
        return True
        
    except Exception as e:
        print(f"[MEMORY] Error saving: {e}")
        return False


def save_file_change(
    file_path: str,
    description: str,
    change_type: str = "modified",
    conversation_id: Optional[int] = None,
    project: Optional[str] = None
) -> bool:
    """
    Guarda un cambio de archivo en la memoria.
    
    Args:
        file_path: Ruta del archivo modificado
        description: Descripción del cambio realizado
        change_type: Tipo de cambio (created, modified, deleted)
        conversation_id: ID de la conversación
        project: Nombre del proyecto
    """
    content = f"Archivo {change_type}: {file_path} - {description}"
    
    return save_memory(
        content=content,
        memory_type="file_change",
        metadata={
            "file_path": file_path,
            "change_type": change_type,
            "description": description
        },
        conversation_id=conversation_id,
        project=project
    )


def save_command(
    command: str,
    output: str = "",
    exit_code: int = 0,
    conversation_id: Optional[int] = None,
    project: Optional[str] = None
) -> bool:
    """Guarda un comando ejecutado en la memoria."""
    content = f"Comando ejecutado: {command}"
    if output:
        content += f" - Output: {output[:200]}"
    
    return save_memory(
        content=content,
        memory_type="command",
        metadata={
            "command": command,
            "exit_code": exit_code
        },
        conversation_id=conversation_id,
        project=project
    )


def save_agent_action(
    action_type: str,
    description: str,
    details: Optional[Dict] = None,
    conversation_id: Optional[int] = None,
    project: Optional[str] = None
) -> bool:
    """Guarda una acción del agente en la memoria."""
    content = f"Acción {action_type}: {description}"
    
    metadata = {"action_type": action_type}
    if details:
        metadata.update(details)
    
    return save_memory(
        content=content,
        memory_type="action",
        metadata=metadata,
        conversation_id=conversation_id,
        project=project
    )


def retrieve_relevant(
    query: str,
    n_results: int = 5,
    project: Optional[str] = None,
    memory_type: Optional[str] = None
) -> List[Dict]:
    """
    Recupera memorias relevantes basadas en búsqueda semántica.
    
    Args:
        query: Consulta para buscar memorias relacionadas
        n_results: Número de resultados a retornar
        project: Filtrar por proyecto
        memory_type: Filtrar por tipo de memoria
    
    Returns:
        Lista de memorias relevantes con su metadata
    """
    collection = _get_chroma()
    if collection is None:
        return []
    
    try:
        # Construir filtros
        where_filter = None
        if project or memory_type:
            conditions = []
            if project:
                conditions.append({"project": project})
            if memory_type:
                conditions.append({"type": memory_type})
            
            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}
        
        # Buscar
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count() or 1),
            where=where_filter
        )
        
        # Formatear resultados
        memories = []
        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                memory = {
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results.get('distances') else None
                }
                memories.append(memory)
        
        print(f"[MEMORY] Retrieved {len(memories)} memories for: {query[:50]}...")
        return memories
        
    except Exception as e:
        print(f"[MEMORY] Error retrieving: {e}")
        return []


def get_context_for_message(
    user_message: str,
    project: Optional[str] = None,
    n_results: int = 5
) -> str:
    """
    Genera contexto relevante para incluir en el prompt del agente.
    
    Args:
        user_message: Mensaje del usuario
        project: Proyecto actual
        n_results: Número de memorias a incluir
    
    Returns:
        String formateado con el contexto relevante
    """
    memories = retrieve_relevant(query=user_message, n_results=n_results, project=project)
    
    if not memories:
        return ""
    
    # Formatear contexto
    context_lines = ["<RELEVANT_MEMORY>", "Información relevante del historial:"]
    
    for i, mem in enumerate(memories, 1):
        meta = mem.get('metadata', {})
        date = meta.get('date', 'unknown')
        time = meta.get('time', '')
        mem_type = meta.get('type', 'memory')
        
        context_lines.append(f"\n{i}. [{date} {time}] ({mem_type})")
        context_lines.append(f"   {mem['content']}")
        
        # Agregar detalles relevantes
        if meta.get('file_path'):
            context_lines.append(f"   Archivo: {meta['file_path']}")
    
    context_lines.append("</RELEVANT_MEMORY>")
    
    return "\n".join(context_lines)


def get_recent_changes(
    project: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Obtiene los cambios más recientes (sin búsqueda semántica).
    """
    collection = _get_chroma()
    if collection is None:
        return []
    
    try:
        # Obtener todos y ordenar por timestamp
        where_filter = {"type": "file_change"}
        if project:
            where_filter = {"$and": [{"type": "file_change"}, {"project": project}]}
        
        results = collection.get(
            where=where_filter,
            limit=limit
        )
        
        changes = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents']):
                changes.append({
                    "content": doc,
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                })
        
        # Ordenar por timestamp (más reciente primero)
        changes.sort(key=lambda x: x.get('metadata', {}).get('timestamp', ''), reverse=True)
        
        return changes[:limit]
        
    except Exception as e:
        print(f"[MEMORY] Error getting recent: {e}")
        return []


def clear_memory(project: Optional[str] = None) -> bool:
    """Limpia la memoria (todo o solo de un proyecto)."""
    collection = _get_chroma()
    if collection is None:
        return False
    
    try:
        if project:
            # Obtener IDs del proyecto
            results = collection.get(where={"project": project})
            if results and results['ids']:
                collection.delete(ids=results['ids'])
                print(f"[MEMORY] Cleared {len(results['ids'])} memories for project: {project}")
        else:
            # Limpiar todo
            # ChromaDB no tiene clear(), hay que recrear la colección
            global _collection
            _chromadb.delete_collection("agent_memory")
            _collection = _chromadb.create_collection(
                name="agent_memory",
                metadata={"description": "Agent conversation and action memory"}
            )
            print("[MEMORY] All memories cleared")
        
        return True
        
    except Exception as e:
        print(f"[MEMORY] Error clearing: {e}")
        return False


def get_memory_stats() -> Dict:
    """Obtiene estadísticas de la memoria."""
    collection = _get_chroma()
    if collection is None:
        return {"status": "unavailable"}
    
    try:
        count = collection.count()
        return {
            "status": "active",
            "total_memories": count,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
