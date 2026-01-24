"""
Endpoints API para Code Embeddings Profesional
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import asyncio

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])

# Importar el módulo de embeddings
try:
    from core.code_embeddings_pro import get_embeddings, CodeEmbeddingsPro
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class SearchRequest(BaseModel):
    query: str
    n_results: int = 10
    language: Optional[str] = None


class IndexRequest(BaseModel):
    workspace: Optional[str] = "/workspace/project/test03"


# Estado del indexado
indexing_status = {
    "in_progress": False,
    "last_result": None
}


@router.get("/status")
async def embeddings_status():
    """Estado del sistema de embeddings"""
    if not EMBEDDINGS_AVAILABLE:
        return {
            "available": False,
            "error": "ChromaDB no instalado"
        }
    
    try:
        embeddings = get_embeddings()
        stats = embeddings.get_stats()
        return {
            "available": True,
            "indexed": stats['total_chunks'] > 0,
            "stats": stats,
            "indexing_in_progress": indexing_status["in_progress"]
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.post("/index")
async def index_workspace(request: IndexRequest, background_tasks: BackgroundTasks):
    """Indexa el workspace en background"""
    if not EMBEDDINGS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Embeddings no disponible")
    
    if indexing_status["in_progress"]:
        return {
            "status": "already_running",
            "message": "Indexación ya en progreso"
        }
    
    def do_index():
        indexing_status["in_progress"] = True
        try:
            embeddings = get_embeddings(request.workspace)
            result = embeddings.index_workspace()
            indexing_status["last_result"] = result
        finally:
            indexing_status["in_progress"] = False
    
    background_tasks.add_task(do_index)
    
    return {
        "status": "started",
        "message": "Indexación iniciada en background"
    }


@router.post("/search")
async def search_code(request: SearchRequest):
    """Búsqueda semántica de código"""
    if not EMBEDDINGS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Embeddings no disponible")
    
    try:
        embeddings = get_embeddings()
        results = embeddings.search(
            query=request.query,
            n_results=request.n_results,
            filter_language=request.language
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@router.post("/similar")
async def find_similar(code: str, n_results: int = 5):
    """Encuentra código similar"""
    if not EMBEDDINGS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Embeddings no disponible")
    
    try:
        embeddings = get_embeddings()
        results = embeddings.find_similar(code, n_results)
        
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/indexing-status")
async def get_indexing_status():
    """Estado de la indexación"""
    return {
        "in_progress": indexing_status["in_progress"],
        "last_result": indexing_status["last_result"]
    }
