"""
Endpoints API para Codemaps - Grafo de dependencias visual
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.codemaps import CodemapGenerator, get_generator

router = APIRouter(prefix="/api/codemap", tags=["codemap"])


class ScanRequest(BaseModel):
    """Request para escanear directorio"""
    workspace: str
    max_files: int = 150


class FileDetailsRequest(BaseModel):
    """Request para detalles de archivo"""
    workspace: str
    file_path: str


@router.post("/scan")
async def scan_workspace(request: ScanRequest):
    """
    Escanea un directorio y genera el grafo de dependencias.
    
    Analiza archivos Python y JavaScript usando AST para extraer:
    - Imports/dependencias
    - Funciones definidas
    - Clases definidas
    
    Returns:
        Grafo con nodes y edges para visualización D3.js
    """
    try:
        generator = get_generator()
        result = generator.scan_directory(
            request.workspace, 
            max_files=request.max_files
        )
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "graph": {"nodes": [], "edges": []},
                "stats": {}
            }
        
        return {
            "success": True,
            "graph": {
                "nodes": result["nodes"],
                "edges": result["edges"]
            },
            "stats": result["stats"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file-details")
async def get_file_details(request: FileDetailsRequest):
    """Obtiene detalles de un archivo específico"""
    try:
        generator = get_generator()
        details = generator.get_file_details(
            request.file_path,
            request.workspace
        )
        
        if not details:
            raise HTTPException(status_code=404, detail="Archivo no encontrado o no soportado")
        
        return {
            "success": True,
            "details": details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Estado del sistema de Codemaps"""
    return {
        "status": "active",
        "features": [
            "Análisis AST de Python",
            "Análisis regex de JavaScript/TypeScript",
            "Extracción de imports, funciones, clases",
            "Grafo de dependencias interactivo",
            "Visualización D3.js force-directed"
        ],
        "supported_extensions": [".py", ".js", ".jsx", ".ts", ".tsx"]
    }
