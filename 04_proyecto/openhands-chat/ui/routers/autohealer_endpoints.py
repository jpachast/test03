"""
Endpoints API para el Auto-Healer
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.auto_healer import get_auto_healer, HealingStatus

router = APIRouter(prefix="/api/autohealer", tags=["autohealer"])


class HealCodeRequest(BaseModel):
    """Request para ejecutar código con auto-healing"""
    code: str
    language: Optional[str] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = 5


class HealingResponse(BaseModel):
    """Response de una sesión de healing"""
    id: str
    status: str
    language: str
    attempts_count: int
    final_output: Optional[str] = None
    total_time: float
    success: bool


@router.post("/heal", response_model=HealingResponse)
async def heal_code(request: HealCodeRequest):
    """
    Ejecuta código con auto-healing.
    
    Si el código falla, el sistema:
    1. Analiza el error
    2. Intenta corregirlo automáticamente
    3. Reintenta la ejecución
    4. Repite hasta éxito o máximo de intentos
    """
    try:
        healer = get_auto_healer()
        
        # Ajustar max_retries si se especifica
        if request.max_retries:
            healer.max_retries = request.max_retries
        
        session = await healer.heal_code(
            code=request.code,
            language=request.language,
            timeout=request.timeout
        )
        
        return HealingResponse(
            id=session.id,
            status=session.status.value,
            language=session.language,
            attempts_count=len(session.attempts),
            final_output=session.final_output[:2000] if session.final_output else None,
            total_time=session.total_time,
            success=session.status == HealingStatus.SUCCESS
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Obtiene los detalles de una sesión de healing"""
    healer = get_auto_healer()
    session = healer.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    return session.to_dict()


@router.get("/sessions")
async def list_sessions(limit: int = 20):
    """Lista las últimas sesiones de healing"""
    healer = get_auto_healer()
    sessions = healer.list_sessions(limit)
    
    return {
        "sessions": [s.to_dict() for s in sessions],
        "total": len(sessions)
    }


@router.get("/statistics")
async def get_statistics():
    """Retorna estadísticas del auto-healer"""
    healer = get_auto_healer()
    return healer.get_statistics()


@router.get("/status")
async def get_status():
    """Estado del auto-healer"""
    healer = get_auto_healer()
    stats = healer.get_statistics()
    
    return {
        "status": "active",
        "max_retries": healer.max_retries,
        "has_llm_fixer": healer.llm_fixer is not None,
        "supported_languages": list(healer.ERROR_PATTERNS.keys()),
        "statistics": stats
    }


@router.post("/test")
async def test_auto_healing():
    """
    Endpoint de prueba que ejecuta código con error conocido
    para demostrar el auto-healing.
    """
    # Código con error de módulo faltante
    test_code = '''
# Este código tiene un error que será auto-corregido
import requests_fake_module  # Módulo que no existe

print("Si ves esto, el módulo fue instalado o manejado")
'''
    
    # Código alternativo más simple para probar
    test_code_simple = '''
# Test de auto-healing con variable no definida
result = undefined_var + 10
print(f"Resultado: {result}")
'''
    
    healer = get_auto_healer()
    session = await healer.heal_code(test_code_simple, 'python')
    
    return {
        "test_description": "Código con variable no definida",
        "result": session.to_dict()
    }
