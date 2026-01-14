"""Rutas de conversaciones"""
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.database import Database

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
db = Database()

# Estado global del workspace
current_workspace = None


class NewConversationRequest(BaseModel):
    project_id: int = None
    title: str = "Nueva conversación"


def get_current_workspace():
    return current_workspace


def set_current_workspace(path):
    global current_workspace
    current_workspace = path


@router.get("")
async def get_conversations(limit: int = 50):
    """Obtener todas las conversaciones recientes"""
    return {"conversations": db.get_all_conversations(limit)}


@router.post("")
async def create_conversation(request: NewConversationRequest):
    """Crear nueva conversación"""
    conv_id = db.create_conversation(request.project_id, request.title)
    return {"success": True, "conversation_id": conv_id}


@router.get("/{conv_id}")
async def get_conversation(conv_id: int):
    """Obtener una conversación con sus mensajes"""
    global current_workspace
    
    conversations = db.get_all_conversations()
    conv = next((c for c in conversations if c['id'] == conv_id), None)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    project = db.get_project(conv['project_id'])
    if project and project.get('path'):
        current_workspace = project['path']
    
    messages = db.get_messages(conv_id)
    
    return {
        "conversation": conv,
        "messages": messages,
        "workspace": current_workspace
    }


@router.put("/{conv_id}")
async def update_conversation(conv_id: int, request: dict = None):
    """Actualizar conversación"""
    title = request.get('title') if request else None
    status = request.get('status') if request else None
    db.update_conversation(conv_id, title, status)
    return {"success": True}


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: int):
    """Eliminar conversación y su carpeta"""
    conversations = db.get_all_conversations()
    conv = next((c for c in conversations if c['id'] == conv_id), None)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    project = db.get_project(conv['project_id'])
    
    if project and project.get('path'):
        project_path = Path(project['path'])
        if project_path.exists():
            shutil.rmtree(project_path)
    
    db.delete_conversation(conv_id)
    if project:
        db.delete_project(conv['project_id'])
    
    return {"success": True}


@router.get("/project/{project_id}")
async def get_project_conversations(project_id: int):
    """Obtener conversaciones de un proyecto"""
    return {"conversations": db.get_conversations_by_project(project_id)}


@router.get("/{conversation_id}/git-status")
async def get_git_status(conversation_id: int):
    """Obtener estado actual de git del workspace"""
    import subprocess
    
    conv = db.get_conversation(conversation_id, by_conv_id=True)
    if not conv:
        return {"error": "Conversation not found"}
    
    workspace_path = conv.get('workspace_path')
    if not workspace_path:
        return {"branch": None}
    
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        branch = result.stdout.strip() if result.returncode == 0 else None
        return {"branch": branch}
    except Exception as e:
        return {"branch": None, "error": str(e)}


def get_active_sdk_conversations():
    """Obtener referencia a las conversaciones activas (evita import circular)"""
    from ui.routers.chat import active_sdk_conversations
    return active_sdk_conversations


@router.post("/{conversation_id}/pause")
async def pause_conversation(conversation_id: int):
    """Pausar el agente de una conversación usando el método del SDK"""
    conv = get_active_sdk_conversations().get(conversation_id)
    if conv:
        try:
            conv.pause()  # Método real del SDK
            return {"success": True, "status": "paused"}
        except Exception as e:
            return {"success": False, "status": "error", "message": str(e)}
    return {"success": False, "status": "not_running", "message": "No hay agente activo"}


@router.post("/{conversation_id}/resume")
async def resume_conversation(conversation_id: int):
    """Reanudar el agente de una conversación"""
    conv = get_active_sdk_conversations().get(conversation_id)
    if conv:
        try:
            # El SDK reanuda llamando run() de nuevo
            import threading
            def resume_run():
                try:
                    conv.run()
                except Exception as e:
                    print(f"Error resuming: {e}")
            
            thread = threading.Thread(target=resume_run)
            thread.start()
            return {"success": True, "status": "running"}
        except Exception as e:
            return {"success": False, "status": "error", "message": str(e)}
    return {"success": False, "status": "not_running", "message": "No hay agente activo"}


@router.get("/{conversation_id}/agent-status")
async def get_agent_status(conversation_id: int):
    """Obtener estado del agente"""
    conv = get_active_sdk_conversations().get(conversation_id)
    if conv:
        # Verificar estado real del SDK
        try:
            from openhands.sdk.conversation import ConversationExecutionStatus
            status = conv.state.execution_status
            if status == ConversationExecutionStatus.RUNNING:
                return {"status": "running"}
            elif status == ConversationExecutionStatus.PAUSED:
                return {"status": "paused"}
            elif status == ConversationExecutionStatus.FINISHED:
                return {"status": "finished"}
            else:
                return {"status": str(status.value) if hasattr(status, 'value') else str(status)}
        except Exception as e:
            return {"status": "running"}  # Asumir running si hay conversación activa
    return {"status": "idle"}
