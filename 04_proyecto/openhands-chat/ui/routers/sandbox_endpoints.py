"""
Endpoints API para el Sandbox de Ejecución de Código
CON AUTO-FIX INTEGRADO: Cuando hay error, intenta corregir automáticamente
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
import os

# Añadir path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.sandbox import get_sandbox, run_code, ExecutionResult, ExecutionStatus

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])


class ExecuteCodeRequest(BaseModel):
    """Request para ejecutar código"""
    code: str
    language: Optional[str] = None  # Auto-detecta si no se especifica
    timeout: Optional[int] = None
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    auto_fix: bool = True  # Auto-fix habilitado por defecto


class InstallPackageRequest(BaseModel):
    """Request para instalar un paquete"""
    package: str
    language: str = "python"


class ExecutionResponse(BaseModel):
    """Response de una ejecución"""
    id: str
    language: str
    stdout: str
    stderr: str
    exit_code: int
    status: str
    execution_time: float
    error_analysis: Optional[str] = None
    suggested_fix: Optional[str] = None
    # Campos de Auto-Fix
    auto_fixed: bool = False
    original_code: Optional[str] = None
    fix_applied: Optional[str] = None
    fix_iterations: int = 0


@router.post("/execute", response_model=ExecutionResponse)
async def execute_code(request: ExecuteCodeRequest):
    """
    Ejecuta código en el sandbox.
    
    Soporta: Python, JavaScript, TypeScript, Bash, Shell
    
    El lenguaje se auto-detecta si no se especifica.
    
    AUTO-FIX: Si hay error y auto_fix=True, intenta corregir automáticamente.
    """
    try:
        sandbox = get_sandbox()
        result = await sandbox.execute_async(
            code=request.code,
            language=request.language,
            timeout=request.timeout,
            env=request.env,
            cwd=request.cwd
        )
        
        auto_fixed = False
        original_code = None
        fix_applied = None
        fix_iterations = 0
        
        # Si hay error y auto_fix está habilitado, intentar corregir
        if result.status == ExecutionStatus.ERROR and request.auto_fix:
            try:
                from core.auto_fix import get_auto_fixer
                
                fixer = get_auto_fixer(sandbox)
                fix_result = await fixer.auto_fix(
                    code=request.code,
                    language=result.language,
                    timeout=request.timeout or 30,
                    apply_fixes=True,
                    verify_fixes=True
                )
                
                # Si el auto-fix tuvo éxito, usar el resultado corregido
                if fix_result.status.value in ['success', 'partial_success']:
                    auto_fixed = True
                    original_code = request.code
                    fix_applied = fix_result.iterations[-1].fix_description if fix_result.iterations else "Auto-fix aplicado"
                    fix_iterations = len(fix_result.iterations)
                    
                    # Actualizar result con los valores del código corregido
                    result = ExecutionResult(
                        id=result.id,
                        language=result.language,
                        code=fix_result.final_code,
                        stdout=fix_result.final_output,
                        stderr="" if fix_result.verified else fix_result.error_message,
                        exit_code=0 if fix_result.verified else 1,
                        status=ExecutionStatus.SUCCESS if fix_result.verified else ExecutionStatus.ERROR,
                        execution_time=fix_result.total_time,
                        created_at=result.created_at,
                        error_analysis=f"Auto-fix aplicado: {fix_applied}",
                        suggested_fix=None
                    )
            except Exception as fix_error:
                # Si falla el auto-fix, continuar con el resultado original
                pass
        
        return ExecutionResponse(
            id=result.id,
            language=result.language,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            status=result.status.value,
            execution_time=result.execution_time,
            error_analysis=result.error_analysis,
            suggested_fix=result.suggested_fix,
            auto_fixed=auto_fixed,
            original_code=original_code,
            fix_applied=fix_applied,
            fix_iterations=fix_iterations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/python", response_model=ExecutionResponse)
async def execute_python(request: ExecuteCodeRequest):
    """Ejecuta código Python específicamente"""
    request.language = "python"
    return await execute_code(request)


@router.post("/execute/javascript", response_model=ExecutionResponse)
async def execute_javascript(request: ExecuteCodeRequest):
    """Ejecuta código JavaScript específicamente"""
    request.language = "javascript"
    return await execute_code(request)


@router.post("/execute/bash", response_model=ExecutionResponse)
async def execute_bash(request: ExecuteCodeRequest):
    """Ejecuta código Bash específicamente"""
    request.language = "bash"
    return await execute_code(request)


@router.post("/install", response_model=ExecutionResponse)
async def install_package(request: InstallPackageRequest):
    """
    Instala un paquete.
    
    - Python: pip install <package>
    - JavaScript: npm install <package>
    """
    try:
        sandbox = get_sandbox()
        result = sandbox.install_package(request.package, request.language)
        
        return ExecutionResponse(
            id=result.id,
            language=result.language,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            status=result.status.value,
            execution_time=result.execution_time,
            error_analysis=result.error_analysis,
            suggested_fix=result.suggested_fix
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """Retorna los lenguajes soportados por el sandbox"""
    sandbox = get_sandbox()
    return {
        "languages": sandbox.get_supported_languages(),
        "default": "python"
    }


@router.get("/history")
async def get_execution_history(limit: int = 20):
    """Retorna el historial de ejecuciones"""
    sandbox = get_sandbox()
    executions = sandbox.list_executions(limit)
    
    return {
        "executions": [
            {
                "id": e.id,
                "language": e.language,
                "status": e.status.value,
                "exit_code": e.exit_code,
                "execution_time": e.execution_time,
                "created_at": e.created_at,
                "code_preview": e.code[:100] + "..." if len(e.code) > 100 else e.code
            }
            for e in executions
        ],
        "total": len(executions)
    }


@router.get("/execution/{execution_id}")
async def get_execution(execution_id: str):
    """Obtiene los detalles de una ejecución específica"""
    sandbox = get_sandbox()
    result = sandbox.get_execution(execution_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")
    
    return result.to_dict()


@router.post("/cancel/{execution_id}")
async def cancel_execution(execution_id: str):
    """Cancela una ejecución en curso"""
    sandbox = get_sandbox()
    success = sandbox.cancel_execution(execution_id)
    
    return {
        "success": success,
        "message": "Ejecución cancelada" if success else "No se pudo cancelar o no existe"
    }


@router.delete("/history")
async def clear_history():
    """Limpia el historial de ejecuciones"""
    sandbox = get_sandbox()
    sandbox.clear_history()
    return {"success": True, "message": "Historial limpiado"}


@router.get("/status")
async def get_sandbox_status():
    """Retorna el estado del sandbox"""
    sandbox = get_sandbox()
    running = len(sandbox.running_processes)
    total_executions = len(sandbox.executions)
    
    # Contar por estado
    status_counts = {}
    for e in sandbox.executions.values():
        status = e.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "status": "active",
        "workspace_dir": sandbox.workspace_dir,
        "running_processes": running,
        "total_executions": total_executions,
        "executions_by_status": status_counts,
        "supported_languages": list(sandbox.SUPPORTED_LANGUAGES.keys())
    }
