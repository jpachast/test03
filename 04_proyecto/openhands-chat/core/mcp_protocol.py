"""
MCP Protocol - Model Context Protocol Implementation

Implementación real de gestión de contexto para LLMs:
- Contexto persistente entre mensajes
- Comunicación bidireccional con el modelo
- Gestión de memoria de conversación
- Inyección dinámica de contexto
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class ContextType(str, Enum):
    """Tipos de contexto MCP"""
    SYSTEM = "system"           # Instrucciones del sistema
    PROJECT = "project"         # Contexto del proyecto
    FILE = "file"               # Archivos abiertos/relevantes
    CONVERSATION = "conversation"  # Historial de conversación
    TOOL_RESULT = "tool_result"   # Resultados de herramientas
    USER_PREFERENCE = "preference"  # Preferencias del usuario
    MEMORY = "memory"           # Memoria a largo plazo


@dataclass
class ContextItem:
    """Un item de contexto en MCP"""
    id: str
    type: ContextType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10, mayor = más importante
    tokens: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "content_length": len(self.content),
            "metadata": self.metadata,
            "priority": self.priority,
            "tokens": self.tokens,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class MCPSession:
    """Sesión MCP para una conversación"""
    session_id: str
    conversation_id: int
    contexts: Dict[str, ContextItem] = field(default_factory=dict)
    max_tokens: int = 100000  # Límite de tokens de contexto
    current_tokens: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "context_count": len(self.contexts),
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "token_usage": f"{(self.current_tokens / self.max_tokens * 100):.1f}%",
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }


class MCPProtocol:
    """
    Model Context Protocol - Gestión de contexto para LLMs
    
    Funcionalidades:
    - Mantiene contexto persistente entre mensajes
    - Prioriza contexto por relevancia
    - Gestiona límites de tokens
    - Permite inyección dinámica de contexto
    """
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        self._sessions: Dict[str, MCPSession] = {}
        self._default_system_prompt = """Eres un asistente de programación experto. 
Tienes acceso al contexto del proyecto y puedes ayudar con código, debugging y arquitectura."""
    
    def _generate_id(self, content: str) -> str:
        """Genera ID único para contenido"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _estimate_tokens(self, text: str) -> int:
        """Estima tokens (aproximado: 4 chars = 1 token)"""
        return len(text) // 4
    
    # ==========================================
    # Gestión de Sesiones
    # ==========================================
    
    def get_or_create_session(self, conversation_id: int) -> MCPSession:
        """Obtiene o crea una sesión MCP"""
        session_key = f"conv_{conversation_id}"
        
        if session_key not in self._sessions:
            self._sessions[session_key] = MCPSession(
                session_id=session_key,
                conversation_id=conversation_id
            )
            # Agregar contexto del sistema por defecto
            self.add_context(
                conversation_id=conversation_id,
                context_type=ContextType.SYSTEM,
                content=self._default_system_prompt,
                priority=10,
                metadata={"source": "default"}
            )
        
        return self._sessions[session_key]
    
    def get_session(self, conversation_id: int) -> Optional[MCPSession]:
        """Obtiene sesión si existe"""
        session_key = f"conv_{conversation_id}"
        return self._sessions.get(session_key)
    
    # ==========================================
    # Gestión de Contexto
    # ==========================================
    
    def add_context(
        self,
        conversation_id: int,
        context_type: ContextType,
        content: str,
        priority: int = 5,
        metadata: Dict = None
    ) -> ContextItem:
        """
        Agrega contexto a la sesión MCP.
        
        Args:
            conversation_id: ID de la conversación
            context_type: Tipo de contexto
            content: Contenido del contexto
            priority: Prioridad 1-10
            metadata: Metadatos adicionales
        
        Returns:
            ContextItem creado
        """
        session = self.get_or_create_session(conversation_id)
        
        context_id = self._generate_id(f"{context_type.value}_{content[:100]}")
        tokens = self._estimate_tokens(content)
        
        item = ContextItem(
            id=context_id,
            type=context_type,
            content=content,
            metadata=metadata or {},
            priority=priority,
            tokens=tokens
        )
        
        # Verificar límite de tokens
        if session.current_tokens + tokens > session.max_tokens:
            self._evict_low_priority_context(session, tokens)
        
        session.contexts[context_id] = item
        session.current_tokens += tokens
        session.last_updated = datetime.now()
        
        logger.info(f"[MCP] Contexto agregado: {context_type.value} ({tokens} tokens)")
        
        return item
    
    def remove_context(self, conversation_id: int, context_id: str) -> bool:
        """Elimina un contexto específico"""
        session = self.get_session(conversation_id)
        if not session or context_id not in session.contexts:
            return False
        
        item = session.contexts.pop(context_id)
        session.current_tokens -= item.tokens
        session.last_updated = datetime.now()
        
        return True
    
    def update_context(
        self,
        conversation_id: int,
        context_id: str,
        content: str = None,
        priority: int = None
    ) -> Optional[ContextItem]:
        """Actualiza un contexto existente"""
        session = self.get_session(conversation_id)
        if not session or context_id not in session.contexts:
            return None
        
        item = session.contexts[context_id]
        
        if content is not None:
            old_tokens = item.tokens
            item.content = content
            item.tokens = self._estimate_tokens(content)
            session.current_tokens += (item.tokens - old_tokens)
        
        if priority is not None:
            item.priority = priority
        
        session.last_updated = datetime.now()
        return item
    
    def _evict_low_priority_context(self, session: MCPSession, needed_tokens: int):
        """Elimina contexto de baja prioridad para liberar espacio"""
        # Ordenar por prioridad (menor primero)
        sorted_contexts = sorted(
            session.contexts.items(),
            key=lambda x: (x[1].priority, x[1].created_at)
        )
        
        freed_tokens = 0
        to_remove = []
        
        for ctx_id, ctx in sorted_contexts:
            if ctx.type == ContextType.SYSTEM:
                continue  # No eliminar contexto del sistema
            
            to_remove.append(ctx_id)
            freed_tokens += ctx.tokens
            
            if freed_tokens >= needed_tokens:
                break
        
        for ctx_id in to_remove:
            item = session.contexts.pop(ctx_id)
            session.current_tokens -= item.tokens
            logger.info(f"[MCP] Contexto evicted: {ctx_id} ({item.tokens} tokens)")
    
    # ==========================================
    # Construcción de Prompt con Contexto
    # ==========================================
    
    def build_context_prompt(self, conversation_id: int) -> str:
        """
        Construye el prompt completo con todo el contexto relevante.
        
        Ordena por prioridad y tipo para máxima efectividad.
        """
        session = self.get_session(conversation_id)
        if not session:
            return self._default_system_prompt
        
        # Agrupar por tipo y ordenar por prioridad
        grouped: Dict[ContextType, List[ContextItem]] = {}
        for ctx in session.contexts.values():
            if ctx.type not in grouped:
                grouped[ctx.type] = []
            grouped[ctx.type].append(ctx)
        
        # Ordenar cada grupo por prioridad
        for ctx_type in grouped:
            grouped[ctx_type].sort(key=lambda x: x.priority, reverse=True)
        
        # Construir prompt en orden
        parts = []
        
        # 1. Sistema
        if ContextType.SYSTEM in grouped:
            for ctx in grouped[ContextType.SYSTEM]:
                parts.append(f"[SYSTEM]\n{ctx.content}")
        
        # 2. Proyecto
        if ContextType.PROJECT in grouped:
            parts.append("\n[PROJECT CONTEXT]")
            for ctx in grouped[ContextType.PROJECT]:
                parts.append(ctx.content)
        
        # 3. Archivos
        if ContextType.FILE in grouped:
            parts.append("\n[RELEVANT FILES]")
            for ctx in grouped[ContextType.FILE]:
                filename = ctx.metadata.get("filename", "unknown")
                parts.append(f"--- {filename} ---\n{ctx.content}")
        
        # 4. Memoria
        if ContextType.MEMORY in grouped:
            parts.append("\n[MEMORY]")
            for ctx in grouped[ContextType.MEMORY]:
                parts.append(ctx.content)
        
        # 5. Resultados de herramientas
        if ContextType.TOOL_RESULT in grouped:
            parts.append("\n[TOOL RESULTS]")
            for ctx in grouped[ContextType.TOOL_RESULT][:5]:  # Limitar
                parts.append(ctx.content)
        
        return "\n\n".join(parts)
    
    def get_contexts_for_message(
        self,
        conversation_id: int,
        user_message: str
    ) -> List[Dict]:
        """
        Obtiene contextos relevantes para un mensaje específico.
        
        Puede usarse para inyección dinámica basada en el mensaje.
        """
        session = self.get_session(conversation_id)
        if not session:
            return []
        
        # Por ahora retorna todos, pero podría filtrar por relevancia
        relevant = []
        for ctx in session.contexts.values():
            relevant.append({
                "type": ctx.type.value,
                "content": ctx.content,
                "priority": ctx.priority
            })
        
        return sorted(relevant, key=lambda x: x["priority"], reverse=True)
    
    # ==========================================
    # Helpers para tipos específicos
    # ==========================================
    
    def add_file_context(
        self,
        conversation_id: int,
        filename: str,
        content: str,
        priority: int = 6
    ) -> ContextItem:
        """Agrega un archivo al contexto"""
        return self.add_context(
            conversation_id=conversation_id,
            context_type=ContextType.FILE,
            content=content,
            priority=priority,
            metadata={"filename": filename, "added_at": datetime.now().isoformat()}
        )
    
    def add_tool_result(
        self,
        conversation_id: int,
        tool_name: str,
        result: str,
        priority: int = 4
    ) -> ContextItem:
        """Agrega resultado de herramienta al contexto"""
        return self.add_context(
            conversation_id=conversation_id,
            context_type=ContextType.TOOL_RESULT,
            content=f"[{tool_name}] {result}",
            priority=priority,
            metadata={"tool": tool_name}
        )
    
    def add_memory(
        self,
        conversation_id: int,
        memory: str,
        priority: int = 7
    ) -> ContextItem:
        """Agrega memoria a largo plazo"""
        return self.add_context(
            conversation_id=conversation_id,
            context_type=ContextType.MEMORY,
            content=memory,
            priority=priority,
            metadata={"type": "long_term"}
        )
    
    def set_system_prompt(
        self,
        conversation_id: int,
        prompt: str
    ) -> ContextItem:
        """Establece/actualiza el system prompt"""
        session = self.get_or_create_session(conversation_id)
        
        # Buscar y eliminar system prompt existente
        to_remove = [
            ctx_id for ctx_id, ctx in session.contexts.items()
            if ctx.type == ContextType.SYSTEM
        ]
        for ctx_id in to_remove:
            self.remove_context(conversation_id, ctx_id)
        
        return self.add_context(
            conversation_id=conversation_id,
            context_type=ContextType.SYSTEM,
            content=prompt,
            priority=10,
            metadata={"source": "custom"}
        )
    
    # ==========================================
    # Estadísticas y Debug
    # ==========================================
    
    def get_session_stats(self, conversation_id: int) -> Dict:
        """Obtiene estadísticas de la sesión"""
        session = self.get_session(conversation_id)
        if not session:
            return {"error": "Session not found"}
        
        stats = session.to_dict()
        
        # Contar por tipo
        type_counts = {}
        type_tokens = {}
        for ctx in session.contexts.values():
            t = ctx.type.value
            type_counts[t] = type_counts.get(t, 0) + 1
            type_tokens[t] = type_tokens.get(t, 0) + ctx.tokens
        
        stats["contexts_by_type"] = type_counts
        stats["tokens_by_type"] = type_tokens
        stats["contexts"] = [ctx.to_dict() for ctx in session.contexts.values()]
        
        return stats
    
    def clear_session(self, conversation_id: int) -> bool:
        """Limpia toda la sesión"""
        session_key = f"conv_{conversation_id}"
        if session_key in self._sessions:
            del self._sessions[session_key]
            return True
        return False


# Instancia global
_mcp: Optional[MCPProtocol] = None


def get_mcp() -> MCPProtocol:
    """Obtiene o crea instancia MCP global"""
    global _mcp
    if _mcp is None:
        _mcp = MCPProtocol()
    return _mcp
