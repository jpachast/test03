"""
Endpoints API para MCP Protocol
Model Context Protocol - Gestión de contexto para LLMs
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.mcp_protocol import MCPProtocol, ContextType, get_mcp

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class AddContextRequest(BaseModel):
    """Request para agregar contexto"""
    conversation_id: int
    context_type: str  # system, project, file, conversation, tool_result, preference, memory
    content: str
    priority: int = 5
    metadata: dict = {}


class UpdateContextRequest(BaseModel):
    """Request para actualizar contexto"""
    conversation_id: int
    context_id: str
    content: Optional[str] = None
    priority: Optional[int] = None


class AddFileContextRequest(BaseModel):
    """Request para agregar archivo al contexto"""
    conversation_id: int
    filename: str
    content: str
    priority: int = 6


class SetSystemPromptRequest(BaseModel):
    """Request para establecer system prompt"""
    conversation_id: int
    prompt: str


class AddMemoryRequest(BaseModel):
    """Request para agregar memoria"""
    conversation_id: int
    memory: str
    priority: int = 7


@router.post("/context/add")
async def add_context(request: AddContextRequest):
    """
    Agrega contexto a la sesión MCP.
    
    Tipos válidos: system, project, file, conversation, tool_result, preference, memory
    """
    try:
        mcp = get_mcp()
        
        # Mapear tipo de contexto
        type_map = {
            "system": ContextType.SYSTEM,
            "project": ContextType.PROJECT,
            "file": ContextType.FILE,
            "conversation": ContextType.CONVERSATION,
            "tool_result": ContextType.TOOL_RESULT,
            "preference": ContextType.USER_PREFERENCE,
            "memory": ContextType.MEMORY
        }
        
        ctx_type = type_map.get(request.context_type.lower())
        if not ctx_type:
            raise HTTPException(status_code=400, detail=f"Tipo inválido: {request.context_type}")
        
        item = mcp.add_context(
            conversation_id=request.conversation_id,
            context_type=ctx_type,
            content=request.content,
            priority=request.priority,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "context": item.to_dict(),
            "message": f"Contexto agregado: {item.id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/update")
async def update_context(request: UpdateContextRequest):
    """Actualiza un contexto existente"""
    try:
        mcp = get_mcp()
        
        item = mcp.update_context(
            conversation_id=request.conversation_id,
            context_id=request.context_id,
            content=request.content,
            priority=request.priority
        )
        
        if not item:
            raise HTTPException(status_code=404, detail="Contexto no encontrado")
        
        return {
            "success": True,
            "context": item.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/context/{conversation_id}/{context_id}")
async def remove_context(conversation_id: int, context_id: str):
    """Elimina un contexto específico"""
    mcp = get_mcp()
    
    success = mcp.remove_context(conversation_id, context_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Contexto no encontrado")
    
    return {
        "success": True,
        "message": f"Contexto {context_id} eliminado"
    }


@router.post("/file/add")
async def add_file_context(request: AddFileContextRequest):
    """Agrega un archivo al contexto MCP"""
    try:
        mcp = get_mcp()
        
        item = mcp.add_file_context(
            conversation_id=request.conversation_id,
            filename=request.filename,
            content=request.content,
            priority=request.priority
        )
        
        return {
            "success": True,
            "context": item.to_dict(),
            "message": f"Archivo agregado: {request.filename}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system-prompt")
async def set_system_prompt(request: SetSystemPromptRequest):
    """Establece el system prompt personalizado"""
    try:
        mcp = get_mcp()
        
        item = mcp.set_system_prompt(
            conversation_id=request.conversation_id,
            prompt=request.prompt
        )
        
        return {
            "success": True,
            "context": item.to_dict(),
            "message": "System prompt actualizado"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/add")
async def add_memory(request: AddMemoryRequest):
    """Agrega memoria a largo plazo"""
    try:
        mcp = get_mcp()
        
        item = mcp.add_memory(
            conversation_id=request.conversation_id,
            memory=request.memory,
            priority=request.priority
        )
        
        return {
            "success": True,
            "context": item.to_dict(),
            "message": "Memoria agregada"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{conversation_id}")
async def get_session_stats(conversation_id: int):
    """Obtiene estadísticas y contextos de la sesión MCP"""
    mcp = get_mcp()
    
    stats = mcp.get_session_stats(conversation_id)
    
    if "error" in stats:
        # Crear sesión si no existe
        mcp.get_or_create_session(conversation_id)
        stats = mcp.get_session_stats(conversation_id)
    
    return {
        "success": True,
        "session": stats
    }


@router.get("/prompt/{conversation_id}")
async def get_built_prompt(conversation_id: int):
    """Obtiene el prompt construido con todo el contexto"""
    mcp = get_mcp()
    
    prompt = mcp.build_context_prompt(conversation_id)
    
    return {
        "success": True,
        "prompt": prompt,
        "tokens_estimated": len(prompt) // 4
    }


@router.delete("/session/{conversation_id}")
async def clear_session(conversation_id: int):
    """Limpia toda la sesión MCP"""
    mcp = get_mcp()
    
    success = mcp.clear_session(conversation_id)
    
    return {
        "success": True,
        "cleared": success,
        "message": "Sesión limpiada" if success else "Sesión no existía"
    }


@router.get("/status")
async def get_mcp_status():
    """Estado del sistema MCP"""
    mcp = get_mcp()
    
    active_sessions = len(mcp._sessions)
    total_contexts = sum(
        len(s.contexts) for s in mcp._sessions.values()
    )
    total_tokens = sum(
        s.current_tokens for s in mcp._sessions.values()
    )
    
    return {
        "status": "active",
        "active_sessions": active_sessions,
        "total_contexts": total_contexts,
        "total_tokens": total_tokens,
        "features": [
            "Contexto persistente entre mensajes",
            "Priorización por relevancia",
            "Gestión automática de límites de tokens",
            "Inyección dinámica de contexto",
            "Soporte para archivos, memoria, herramientas"
        ],
        "context_types": [
            "system", "project", "file", "conversation",
            "tool_result", "preference", "memory"
        ]
    }
