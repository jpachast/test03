"""
Endpoints para integración del Sandbox con el Chat
Permite ejecutar código detectado en respuestas del agente
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import traceback

router = APIRouter(prefix="/api/sandbox-chat", tags=["sandbox-chat"])

# Importar el sandbox integrado
try:
    from core.sandbox_integration import integrated_sandbox, process_agent_response
except ImportError:
    integrated_sandbox = None


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    project_path: Optional[str] = None
    auto_fix: bool = False


class ProcessResponseRequest(BaseModel):
    response_text: str
    auto_execute: bool = True


@router.post("/execute")
async def execute_code(request: ExecuteRequest):
    """
    Ejecuta código en el contexto del proyecto
    Con acceso a imports y archivos del proyecto
    """
    if not integrated_sandbox:
        raise HTTPException(status_code=500, detail="Sandbox no disponible")
    
    try:
        if request.project_path:
            integrated_sandbox.project_path = request.project_path
        
        if request.auto_fix:
            result = integrated_sandbox.auto_fix_and_retry(
                request.code, 
                request.language
            )
        else:
            result = integrated_sandbox.execute_in_context(
                request.code, 
                request.language
            )
        
        return {
            "success": result.get("success") or result.get("final_success", False),
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/process-response")
async def process_response(request: ProcessResponseRequest):
    """
    Procesa una respuesta del agente:
    1. Detecta bloques de código
    2. Los ejecuta automáticamente
    3. Retorna resultados
    """
    if not integrated_sandbox:
        raise HTTPException(status_code=500, detail="Sandbox no disponible")
    
    try:
        result = process_agent_response(request.response_text)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": request.response_text,
            "executions": []
        }


@router.get("/status")
async def sandbox_status():
    """Estado del sandbox integrado"""
    return {
        "available": integrated_sandbox is not None,
        "project_path": integrated_sandbox.project_path if integrated_sandbox else None,
        "execution_count": len(integrated_sandbox.execution_history) if integrated_sandbox else 0,
        "features": {
            "auto_execute": True,
            "auto_fix": True,
            "supported_languages": ["python", "bash", "javascript"],
            "project_context": True
        }
    }


@router.post("/analyze-error")
async def analyze_error(code: str, stderr: str, language: str = "python"):
    """Analiza un error y sugiere corrección"""
    if not integrated_sandbox:
        raise HTTPException(status_code=500, detail="Sandbox no disponible")
    
    if language == "python":
        error_type, suggested_fix = integrated_sandbox._analyze_python_error(stderr, code)
        return {
            "error_type": error_type,
            "suggested_fix": suggested_fix,
            "can_auto_fix": suggested_fix is not None
        }
    
    return {
        "error_type": None,
        "suggested_fix": None,
        "can_auto_fix": False
    }


@router.get("/history")
async def get_execution_history(limit: int = 10):
    """Obtiene historial de ejecuciones recientes"""
    if not integrated_sandbox:
        return {"history": []}
    
    history = integrated_sandbox.execution_history[-limit:]
    return {
        "total": len(integrated_sandbox.execution_history),
        "showing": len(history),
        "history": history
    }
