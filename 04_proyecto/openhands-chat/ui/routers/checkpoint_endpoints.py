"""
Endpoints API para Checkpoints - Sistema de snapshots del código
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.checkpoints import CheckpointManager, get_checkpoint_manager

router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])


class CreateCheckpointRequest(BaseModel):
    """Request para crear checkpoint"""
    workspace: str
    name: str
    description: str = ""


class RestoreCheckpointRequest(BaseModel):
    """Request para restaurar checkpoint"""
    checkpoint_id: str
    target_workspace: Optional[str] = None
    dry_run: bool = True  # Por defecto solo preview


class DiffCheckpointsRequest(BaseModel):
    """Request para comparar checkpoints"""
    checkpoint_id_1: str
    checkpoint_id_2: str


class GetFileRequest(BaseModel):
    """Request para obtener archivo"""
    checkpoint_id: str
    file_path: str


@router.post("/create")
async def create_checkpoint(request: CreateCheckpointRequest):
    """
    Crea un nuevo checkpoint del workspace.
    
    Captura el estado actual de todos los archivos de código.
    """
    try:
        manager = get_checkpoint_manager()
        
        checkpoint = manager.create_checkpoint(
            workspace=request.workspace,
            name=request.name,
            description=request.description
        )
        
        return {
            "success": True,
            "checkpoint": checkpoint.to_dict(),
            "message": f"Checkpoint '{request.name}' creado con {len(checkpoint.files)} archivos"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore_checkpoint(request: RestoreCheckpointRequest):
    """
    Restaura un checkpoint al workspace.
    
    Por defecto hace dry_run (preview) para mostrar qué cambiaría.
    """
    try:
        manager = get_checkpoint_manager()
        
        result = manager.restore_checkpoint(
            checkpoint_id=request.checkpoint_id,
            target_workspace=request.target_workspace,
            dry_run=request.dry_run
        )
        
        return {
            "success": result["success"],
            "result": result,
            "message": "Preview de restauración" if request.dry_run else "Checkpoint restaurado"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_checkpoints(limit: int = 20):
    """Lista todos los checkpoints disponibles"""
    manager = get_checkpoint_manager()
    
    checkpoints = manager.list_checkpoints(limit=limit)
    stats = manager.get_stats()
    
    return {
        "success": True,
        "checkpoints": checkpoints,
        "stats": stats
    }


@router.get("/{checkpoint_id}")
async def get_checkpoint(checkpoint_id: str):
    """Obtiene detalles de un checkpoint específico"""
    manager = get_checkpoint_manager()
    
    checkpoint = manager.get_checkpoint(checkpoint_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint no encontrado")
    
    return {
        "success": True,
        "checkpoint": checkpoint.to_dict()
    }


@router.delete("/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str):
    """Elimina un checkpoint"""
    manager = get_checkpoint_manager()
    
    success = manager.delete_checkpoint(checkpoint_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Checkpoint no encontrado")
    
    return {
        "success": True,
        "message": f"Checkpoint {checkpoint_id} eliminado"
    }


@router.post("/diff")
async def diff_checkpoints(request: DiffCheckpointsRequest):
    """Compara dos checkpoints y muestra las diferencias"""
    try:
        manager = get_checkpoint_manager()
        
        diff = manager.diff_checkpoints(
            checkpoint_id_1=request.checkpoint_id_1,
            checkpoint_id_2=request.checkpoint_id_2
        )
        
        return {
            "success": True,
            "diff": diff
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file-content")
async def get_file_content(request: GetFileRequest):
    """Obtiene el contenido de un archivo en un checkpoint"""
    manager = get_checkpoint_manager()
    
    content = manager.get_file_content(
        checkpoint_id=request.checkpoint_id,
        file_path=request.file_path
    )
    
    if content is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el checkpoint")
    
    return {
        "success": True,
        "file_path": request.file_path,
        "content": content
    }


@router.get("/stats/summary")
async def get_stats():
    """Estadísticas del sistema de checkpoints"""
    manager = get_checkpoint_manager()
    
    return {
        "success": True,
        "stats": manager.get_stats()
    }
