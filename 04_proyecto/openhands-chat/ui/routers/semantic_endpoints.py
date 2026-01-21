"""
Endpoints API para Semantic Search
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.semantic_search import SemanticSearch, get_semantic_search, set_semantic_search

router = APIRouter(prefix="/api/semantic", tags=["semantic"])

# Instancia global por workspace
_instances: Dict[str, SemanticSearch] = {}


def get_instance(workspace: str) -> SemanticSearch:
    """Obtiene o crea instancia de SemanticSearch para un workspace"""
    if workspace not in _instances:
        _instances[workspace] = SemanticSearch(workspace)
    return _instances[workspace]


class IndexRequest(BaseModel):
    """Request para indexar un proyecto"""
    workspace: str
    force: bool = False  # Forzar reindexación completa


class SearchRequest(BaseModel):
    """Request para búsqueda semántica"""
    workspace: str
    query: str
    n_results: int = 10


class SimilarRequest(BaseModel):
    """Request para encontrar código similar"""
    workspace: str
    file_path: str
    line: int
    n_results: int = 5


@router.post("/index")
async def index_workspace(request: IndexRequest):
    """
    Indexa un workspace para búsqueda semántica.
    
    Procesa archivos de código, genera chunks semánticos,
    y almacena embeddings en ChromaDB.
    """
    try:
        semantic = get_instance(request.workspace)
        
        if request.force:
            semantic.clear()
        
        stats = semantic.index()
        
        return {
            "success": True,
            "workspace": request.workspace,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def semantic_search(request: SearchRequest):
    """
    Búsqueda semántica en el código.
    
    Permite preguntas en lenguaje natural como:
    - "¿dónde está la autenticación?"
    - "funciones que manejan errores"
    - "código relacionado con base de datos"
    """
    try:
        semantic = get_instance(request.workspace)
        results = semantic.search(request.query, request.n_results)
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar")
async def find_similar(request: SimilarRequest):
    """
    Encuentra código similar a un fragmento específico.
    """
    try:
        semantic = get_instance(request.workspace)
        results = semantic.find_similar(
            request.file_path, 
            request.line, 
            request.n_results
        )
        
        return {
            "success": True,
            "file_path": request.file_path,
            "line": request.line,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(workspace: str):
    """Obtiene estadísticas del índice semántico"""
    try:
        semantic = get_instance(workspace)
        stats = semantic.get_stats()
        
        return {
            "success": True,
            "workspace": workspace,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_index(workspace: str):
    """Limpia el índice semántico de un workspace"""
    try:
        semantic = get_instance(workspace)
        semantic.clear()
        
        return {
            "success": True,
            "message": f"Índice limpiado para {workspace}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Estado del servicio de búsqueda semántica"""
    try:
        # Verificar dependencias
        chromadb_available = False
        sentence_transformers_available = False
        
        try:
            import chromadb
            chromadb_available = True
        except ImportError:
            pass
        
        try:
            from sentence_transformers import SentenceTransformer
            sentence_transformers_available = True
        except ImportError:
            pass
        
        return {
            "status": "active",
            "chromadb_available": chromadb_available,
            "sentence_transformers_available": sentence_transformers_available,
            "active_workspaces": len(_instances),
            "features": [
                "Indexación semántica de código",
                "Búsqueda en lenguaje natural",
                "Detección de código similar",
                "Embeddings locales (sin API externa)",
                "Persistencia con ChromaDB"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
