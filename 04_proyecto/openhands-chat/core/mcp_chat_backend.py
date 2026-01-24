"""
MCP Chat Backend Integration
Integración del MCP Protocol en el flujo de chat para uso automático
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Importar MCP Protocol
try:
    from core.mcp_protocol import MCPProtocol, ContextType, get_mcp
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("[MCP] mcp_protocol no disponible")


class MCPChatBackend:
    """Integración automática de MCP en el chat"""
    
    def __init__(self):
        self.mcp = get_mcp() if MCP_AVAILABLE else None
        self.session_cache = {}
    
    def get_context_for_message(self, conversation_id: int, user_message: str) -> str:
        """
        Obtiene contexto MCP relevante para un mensaje del usuario.
        Este contexto se inyecta en el system prompt del agente.
        """
        if not self.mcp:
            return ""
        
        try:
            # Obtener sesión MCP
            session = self.mcp.get_or_create_session(conversation_id)
            
            # Buscar contexto relevante para el mensaje
            relevant_contexts = []
            
            # 1. Contexto del proyecto (siempre incluir)
            project_ctx = self.mcp.get_contexts_by_type(conversation_id, ContextType.PROJECT)
            if project_ctx:
                relevant_contexts.extend(project_ctx[:2])  # Max 2 items de proyecto
            
            # 2. Memorias relevantes
            memories = self.mcp.get_contexts_by_type(conversation_id, ContextType.MEMORY)
            if memories:
                relevant_contexts.extend(memories[:3])  # Max 3 memorias
            
            # 3. Preferencias del usuario
            prefs = self.mcp.get_contexts_by_type(conversation_id, ContextType.USER_PREFERENCE)
            if prefs:
                relevant_contexts.extend(prefs[:2])  # Max 2 preferencias
            
            # 4. Archivos relevantes mencionados antes
            files = self.mcp.get_contexts_by_type(conversation_id, ContextType.FILE)
            if files:
                relevant_contexts.extend(files[:3])  # Max 3 archivos
            
            if not relevant_contexts:
                return ""
            
            # Formatear contexto para el agente
            context_parts = ["📌 **CONTEXTO MCP ACTIVO:**"]
            for ctx in relevant_contexts:
                type_emoji = {
                    ContextType.PROJECT: "📁",
                    ContextType.MEMORY: "💾",
                    ContextType.USER_PREFERENCE: "⚙️",
                    ContextType.FILE: "📄",
                    ContextType.CONVERSATION: "💬",
                }.get(ctx.type, "📝")
                
                # Truncar contenido largo
                content = ctx.content[:200] + "..." if len(ctx.content) > 200 else ctx.content
                context_parts.append(f"  {type_emoji} [{ctx.type.value}]: {content}")
            
            context_parts.append("")
            context_parts.append("*Usa este contexto para dar respuestas más personalizadas y relevantes.*")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"[MCP] Error obteniendo contexto: {e}")
            return ""
    
    def save_user_message(self, conversation_id: int, message: str):
        """Guarda el mensaje del usuario en el contexto MCP"""
        if not self.mcp:
            return
        
        try:
            self.mcp.add_context(
                conversation_id=conversation_id,
                context_type=ContextType.CONVERSATION,
                content=f"[Usuario]: {message}",
                priority=5,
                metadata={"role": "user", "timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            logger.error(f"[MCP] Error guardando mensaje usuario: {e}")
    
    def save_agent_response(self, conversation_id: int, response: str):
        """Guarda la respuesta del agente y extrae información importante"""
        if not self.mcp:
            return
        
        try:
            # Guardar respuesta en conversación
            self.mcp.add_context(
                conversation_id=conversation_id,
                context_type=ContextType.CONVERSATION,
                content=f"[Agente]: {response[:500]}...",  # Truncar respuestas largas
                priority=5,
                metadata={"role": "assistant", "timestamp": datetime.now().isoformat()}
            )
            
            # Extraer y guardar información importante automáticamente
            self._extract_and_save_important_info(conversation_id, response)
            
        except Exception as e:
            logger.error(f"[MCP] Error guardando respuesta agente: {e}")
    
    def _extract_and_save_important_info(self, conversation_id: int, response: str):
        """Extrae información importante de la respuesta y la guarda como memoria"""
        import re
        
        # Patrones para detectar información importante
        patterns = [
            # Archivos mencionados
            (r'(?:archivo|file|fichero)\s+[`"\']?([\w./\-]+\.\w+)[`"\']?', 'file', "Archivo: {}"),
            # Funciones/métodos
            (r'(?:función|function|método|method|def)\s+[`"\']?(\w+)[`"\']?', 'function', "Función: {}"),
            # Errores y soluciones
            (r'(?:error|problema|issue):\s*(.{20,100})', 'error', "Error encontrado: {}"),
            (r'(?:solución|fix|corregir|arreglar):\s*(.{20,100})', 'solution', "Solución: {}"),
            # Decisiones importantes
            (r'(?:decidí|elegí|usaré|implementaré)\s+(.{20,80})', 'decision', "Decisión: {}"),
        ]
        
        for pattern, info_type, template in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches[:2]:  # Max 2 por tipo
                try:
                    memory_content = template.format(match.strip())
                    self.mcp.add_context(
                        conversation_id=conversation_id,
                        context_type=ContextType.MEMORY,
                        content=memory_content,
                        priority=7,
                        metadata={"extracted_type": info_type, "auto_extracted": True}
                    )
                except Exception:
                    pass
    
    def add_project_context(self, conversation_id: int, project_info: dict):
        """Agrega información del proyecto al contexto MCP"""
        if not self.mcp:
            return
        
        try:
            content = f"Proyecto: {project_info.get('name', 'unknown')}\n"
            content += f"Workspace: {project_info.get('workspace', 'N/A')}\n"
            if project_info.get('repo'):
                content += f"Repositorio: {project_info['repo']}"
            
            self.mcp.add_context(
                conversation_id=conversation_id,
                context_type=ContextType.PROJECT,
                content=content,
                priority=8,
                metadata=project_info
            )
        except Exception as e:
            logger.error(f"[MCP] Error agregando contexto de proyecto: {e}")
    
    def add_user_preference(self, conversation_id: int, preference: str, value: str):
        """Agrega una preferencia del usuario"""
        if not self.mcp:
            return
        
        try:
            self.mcp.add_context(
                conversation_id=conversation_id,
                context_type=ContextType.USER_PREFERENCE,
                content=f"{preference}: {value}",
                priority=6,
                metadata={"preference_key": preference}
            )
        except Exception as e:
            logger.error(f"[MCP] Error agregando preferencia: {e}")
    
    def get_session_stats(self, conversation_id: int) -> dict:
        """Obtiene estadísticas de la sesión MCP"""
        if not self.mcp:
            return {"available": False}
        
        try:
            session = self.mcp.get_or_create_session(conversation_id)
            return {
                "available": True,
                "context_count": len(session.contexts) if session else 0,
                "current_tokens": session.current_tokens if session else 0,
                "session_id": session.session_id if session else None
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# Instancia global
_mcp_backend = None

def get_mcp_backend() -> MCPChatBackend:
    """Obtiene la instancia global del backend MCP"""
    global _mcp_backend
    if _mcp_backend is None:
        _mcp_backend = MCPChatBackend()
    return _mcp_backend
