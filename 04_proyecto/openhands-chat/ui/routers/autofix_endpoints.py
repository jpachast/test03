"""
Endpoints API para Auto-Fix
Loop completo: detectar → corregir → re-ejecutar → verificar
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio

router = APIRouter(prefix="/api/autofix", tags=["autofix"])


class AutoFixRequest(BaseModel):
    """Request para auto-fix de código"""
    code: str
    language: Optional[str] = None
    timeout: Optional[int] = 30
    apply_fixes: bool = True
    verify_fixes: bool = True
    max_iterations: Optional[int] = 5


class AutoFixResponse(BaseModel):
    """Response del auto-fix"""
    success: bool
    session_id: str
    status: str
    language: str
    original_code: str
    final_code: str
    code_changed: bool
    total_fixes_applied: int
    iterations_count: int
    verified: bool
    final_output: str
    error_message: str
    total_time: float
    iterations: List[Dict[str, Any]]


@router.post("/run", response_model=AutoFixResponse)
async def run_auto_fix(request: AutoFixRequest):
    """
    Ejecuta el loop completo de auto-fix.
    
    El sistema:
    1. Ejecuta el código
    2. Si hay error, detecta el tipo
    3. Aplica corrección automática
    4. Re-ejecuta para verificar
    5. Repite hasta éxito o max iteraciones
    """
    try:
        from core.auto_fix import get_auto_fixer
        
        fixer = get_auto_fixer()
        
        # Configurar max iterations si se especificó
        if request.max_iterations:
            fixer.max_iterations = request.max_iterations
        
        # Ejecutar auto-fix
        result = await fixer.auto_fix(
            code=request.code,
            language=request.language,
            timeout=request.timeout,
            apply_fixes=request.apply_fixes,
            verify_fixes=request.verify_fixes
        )
        
        return AutoFixResponse(
            success=result.status.value in ['success', 'partial_success'],
            session_id=result.session_id,
            status=result.status.value,
            language=result.language,
            original_code=result.original_code,
            final_code=result.final_code,
            code_changed=result.original_code != result.final_code,
            total_fixes_applied=result.total_fixes_applied,
            iterations_count=len(result.iterations),
            verified=result.verified,
            final_output=result.final_output,
            error_message=result.error_message,
            total_time=result.total_time,
            iterations=[i.to_dict() for i in result.iterations]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_error(code: str, error: str, language: str = "python"):
    """
    Solo analiza un error sin aplicar fixes.
    Retorna el tipo de error y posibles correcciones.
    """
    try:
        from core.auto_fix import get_auto_fixer
        
        fixer = get_auto_fixer()
        error_type, description, match = fixer.detect_error(language, error)
        fixed_code, fix_description = fixer.apply_fix(language, code, error)
        
        return {
            "error_type": error_type,
            "description": description,
            "has_fix": fixed_code != code,
            "fix_description": fix_description,
            "suggested_code": fixed_code if fixed_code != code else None,
            "diff": fixer.generate_diff(code, fixed_code) if fixed_code != code else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{session_id}")
async def get_result(session_id: str):
    """Obtiene el resultado de una sesión de auto-fix."""
    try:
        from core.auto_fix import get_auto_fixer
        
        fixer = get_auto_fixer()
        result = fixer.get_result(session_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """Obtiene estadísticas del auto-fixer."""
    try:
        from core.auto_fix import get_auto_fixer
        
        fixer = get_auto_fixer()
        return fixer.get_statistics()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-fix")
async def quick_fix(code: str, language: str = "python"):
    """
    Intenta corregir el código rápidamente (1 iteración).
    Útil para sugerencias en tiempo real.
    """
    try:
        from core.auto_fix import get_auto_fixer
        
        fixer = get_auto_fixer()
        
        # Solo 1 iteración para respuesta rápida
        original_max = fixer.max_iterations
        fixer.max_iterations = 1
        
        result = await fixer.auto_fix(
            code=code,
            language=language,
            timeout=10,
            apply_fixes=True,
            verify_fixes=False  # No verificar para rapidez
        )
        
        fixer.max_iterations = original_max
        
        return {
            "success": result.status.value == 'success',
            "code_changed": result.original_code != result.final_code,
            "fixed_code": result.final_code,
            "fix_applied": result.iterations[0].fix_description if result.iterations else None,
            "time": result.total_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
