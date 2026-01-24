"""
API Endpoints for Advanced Features - v2
Incluye MCP y Codebase Embeddings completos
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import json
import os
import asyncio

router = APIRouter(prefix="/api/features", tags=["features"])

# Imports
try:
    from core.advanced_features import (
        DiffPreview, CodemapGenerator, 
        CheckpointManager, get_features_status as _get_basic_features
    )
except ImportError:
    DiffPreview = None
    CodemapGenerator = None
    CheckpointManager = None

try:
    from core.voice_input import VoiceInput, get_voice_input
except ImportError:
    VoiceInput = None
    get_voice_input = None

try:
    from core.mcp_client import get_mcp_client, check_mcp_available
except ImportError:
    get_mcp_client = None
    check_mcp_available = lambda: {"available": False, "error": "MCP no instalado"}

try:
    from core.codebase_embeddings import get_embeddings, check_embeddings_available
except ImportError:
    get_embeddings = None
    check_embeddings_available = lambda: {"available": False, "error": "Embeddings no instalado"}


@router.get("/status")
async def features_status():
    """Get status of all advanced features"""
    mcp_status = check_mcp_available() if check_mcp_available else {"available": False}
    embeddings_status = check_embeddings_available() if check_embeddings_available else {"available": False}
    
    # Voice status
    voice_status = {
        "enabled": True,  # Web Speech siempre disponible
        "backends": ["web_speech"],
        "note": "Web Speech API gratis, Groq/OpenAI opcionales"
    }
    if VoiceInput:
        try:
            voice_status = VoiceInput().get_status()
        except:
            pass
    
    return {
        "mcp": {
            "enabled": mcp_status.get("available", False),
            "npx_available": mcp_status.get("npx_available", False),
            "connected_servers": get_mcp_client().get_status().get("connected_servers", []) if get_mcp_client else []
        },
        "codebase_embeddings": {
            "enabled": embeddings_status.get("available", False),
            "chromadb": embeddings_status.get("chromadb", False),
            "sentence_transformers": embeddings_status.get("sentence_transformers", False)
        },
        "diff_preview": {"enabled": True},
        "codemaps": {"enabled": True, "formats": ["file_structure", "class_diagram", "flowchart"]},
        "checkpoints": {"enabled": True},
        "voice_input": voice_status,
        "image_vision": {"enabled": True, "note": "Ya implementado en chat.py"}
    }


# ============================================
# MCP ENDPOINTS - COMPLETOS
# ============================================

@router.get("/mcp/servers")
async def list_mcp_servers():
    """List available MCP servers"""
    if not get_mcp_client:
        return {"servers": [], "error": "MCP no disponible"}
    
    client = get_mcp_client()
    return {
        "servers": client.list_available_servers(),
        "status": client.get_status()
    }


@router.get("/mcp/status")
async def mcp_status():
    """Get MCP connection status"""
    if not get_mcp_client:
        return {"enabled": False, "error": "MCP no disponible"}
    
    return get_mcp_client().get_status()


@router.post("/mcp/connect")
async def connect_mcp_server(server_id: str = Form(...)):
    """Connect to an MCP server"""
    if not get_mcp_client:
        raise HTTPException(status_code=500, detail="MCP no disponible")
    
    client = get_mcp_client()
    result = await client.connect_server(server_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error desconocido"))
    
    return result


@router.post("/mcp/disconnect")
async def disconnect_mcp_server(server_id: str = Form(...)):
    """Disconnect from an MCP server"""
    if not get_mcp_client:
        raise HTTPException(status_code=500, detail="MCP no disponible")
    
    client = get_mcp_client()
    result = await client.disconnect_server(server_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error desconocido"))
    
    return result


@router.get("/mcp/tools/{server_id}")
async def get_mcp_server_tools(server_id: str):
    """Get tools from a connected MCP server"""
    if not get_mcp_client:
        return {"tools": []}
    
    return {"tools": get_mcp_client().get_server_tools(server_id)}


@router.post("/mcp/call")
async def call_mcp_tool(
    server_id: str = Form(...),
    tool_name: str = Form(...),
    arguments: str = Form("{}")
):
    """Call a tool on an MCP server"""
    if not get_mcp_client:
        raise HTTPException(status_code=500, detail="MCP no disponible")
    
    try:
        args = json.loads(arguments)
    except:
        args = {}
    
    client = get_mcp_client()
    result = await client.call_tool(server_id, tool_name, args)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error desconocido"))
    
    return result


# ============================================
# CODEBASE EMBEDDINGS ENDPOINTS - COMPLETOS
# ============================================

@router.get("/embeddings/status")
async def embeddings_status(workspace: str = "/workspace/project/test03"):
    """Get embeddings status for a workspace"""
    status = check_embeddings_available()
    
    if not status.get("available"):
        return {
            "indexed": False,
            "available": False,
            "error": "Dependencias no instaladas",
            "missing": {
                "chromadb": not status.get("chromadb", False),
                "sentence_transformers": not status.get("sentence_transformers", False)
            }
        }
    
    embeddings = get_embeddings(workspace)
    return embeddings.get_stats()


@router.post("/embeddings/index")
async def index_codebase(
    workspace: str = Form("/workspace/project/test03"),
    force: bool = Form(False)
):
    """Index the codebase for semantic search"""
    if not get_embeddings:
        raise HTTPException(status_code=500, detail="Embeddings no disponible")
    
    embeddings = get_embeddings(workspace)
    result = embeddings.index_codebase(force_reindex=force)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error indexando"))
    
    return result


@router.post("/embeddings/search")
async def search_codebase(
    workspace: str = Form("/workspace/project/test03"),
    query: str = Form(...),
    n_results: int = Form(5)
):
    """Search the codebase using semantic similarity"""
    if not get_embeddings:
        raise HTTPException(status_code=500, detail="Embeddings no disponible")
    
    embeddings = get_embeddings(workspace)
    result = embeddings.search(query, n_results)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error en búsqueda"))
    
    return result


# ============================================
# DIFF PREVIEW ENDPOINTS
# ============================================

@router.post("/diff/generate")
async def generate_diff(
    original: str = Form(...),
    modified: str = Form(...),
    filename: str = Form("file")
):
    """Generate diff between two versions"""
    if not DiffPreview:
        raise HTTPException(status_code=500, detail="DiffPreview no disponible")
    
    result = DiffPreview.generate_diff(original, modified, filename)
    result["html"] = DiffPreview.format_for_display(result)
    return result


# ============================================
# CODEMAPS ENDPOINTS
# ============================================

@router.post("/codemaps/structure")
async def generate_structure_map(
    directory: str = Form(...),
    max_depth: int = Form(3)
):
    """Generate file structure diagram"""
    if not CodemapGenerator:
        raise HTTPException(status_code=500, detail="CodemapGenerator no disponible")
    
    mermaid = CodemapGenerator.generate_file_structure(directory, max_depth)
    return {"mermaid": mermaid, "type": "file_structure"}


@router.post("/codemaps/classes")
async def generate_class_diagram(code: str = Form(...)):
    """Generate class diagram from Python code"""
    if not CodemapGenerator:
        raise HTTPException(status_code=500, detail="CodemapGenerator no disponible")
    
    mermaid = CodemapGenerator.generate_class_diagram(code)
    return {"mermaid": mermaid, "type": "class_diagram"}


@router.post("/codemaps/flow")
async def generate_flow_diagram(description: str = Form(...)):
    """Generate flow diagram"""
    if not CodemapGenerator:
        raise HTTPException(status_code=500, detail="CodemapGenerator no disponible")
    
    mermaid = CodemapGenerator.generate_flow_diagram(description)
    return {"mermaid": mermaid, "type": "flowchart"}


# ============================================
# CHECKPOINT ENDPOINTS
# ============================================

@router.post("/checkpoints/create")
async def create_checkpoint(
    workspace: str = Form(...),
    description: str = Form("")
):
    """Create a new checkpoint"""
    if not CheckpointManager:
        raise HTTPException(status_code=500, detail="CheckpointManager no disponible")
    
    manager = CheckpointManager(workspace)
    return manager.create_checkpoint(description)


@router.get("/checkpoints/list")
async def list_checkpoints(workspace: str):
    """List all checkpoints for a workspace"""
    if not CheckpointManager:
        return {"checkpoints": []}
    
    manager = CheckpointManager(workspace)
    return {"checkpoints": manager.list_checkpoints()}


@router.post("/checkpoints/restore")
async def restore_checkpoint(
    workspace: str = Form(...),
    ref: str = Form(...)
):
    """Restore a specific checkpoint"""
    if not CheckpointManager:
        raise HTTPException(status_code=500, detail="CheckpointManager no disponible")
    
    manager = CheckpointManager(workspace)
    return manager.restore_checkpoint(ref)


# ============================================
# VOICE INPUT ENDPOINTS
# ============================================

@router.post("/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    backend: str = Form("auto"),
    openai_key: str = Form(None),
    groq_key: str = Form(None)
):
    """Transcribe audio to text using selected backend"""
    if not VoiceInput:
        raise HTTPException(status_code=500, detail="VoiceInput no disponible")
    
    voice = VoiceInput(openai_key, groq_key)
    audio_data = await audio.read()
    format_type = audio.filename.split(".")[-1] if audio.filename else "webm"
    
    result = await voice.transcribe(audio_data, format_type, backend)
    return result


@router.get("/voice/status")
async def voice_status(openai_key: str = None, groq_key: str = None):
    """Get voice input status with all backends"""
    if not VoiceInput:
        return {
            "enabled": True,  # Web Speech siempre disponible
            "backends": {
                "web_speech": {
                    "enabled": True,
                    "description": "Reconocimiento de voz del navegador",
                    "requires_key": False,
                    "free": True
                }
            }
        }
    
    return VoiceInput(openai_key, groq_key).get_status()
