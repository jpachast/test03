"""
Auto-Fix Chat Router
Endpoints para integración de auto-fix en conversaciones
"""

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter(prefix="/api/chat/autofix", tags=["chat-autofix"])


@router.post("/detect")
async def detect_and_fix_error(
    code: str = Form(...),
    error_output: str = Form(...),
    language: str = Form("python")
):
    """
    Detecta si hay un error en el output y aplica auto-fix.
    El frontend llama esto cuando detecta un error en la respuesta.
    """
    from core.chat_autofix_integration import (
        detect_error_in_output, try_auto_fix, format_autofix_result
    )
    
    has_error, error_type, error_msg = detect_error_in_output(error_output)
    
    if not has_error:
        return JSONResponse({
            "has_error": False,
            "message": "No se detectó error en el output"
        })
    
    # Intentar auto-fix
    result = await try_auto_fix(code, error_output, language)
    
    if result.get("success") and result.get("code_changed"):
        formatted = format_autofix_result(result)
        return JSONResponse({
            "has_error": True,
            "error_type": error_type,
            "error_message": error_msg,
            "auto_fixed": True,
            "original_code": result.get("original_code"),
            "fixed_code": result.get("fixed_code"),
            "fixes_applied": result.get("fixes_applied"),
            "verified": result.get("verified"),
            "final_output": result.get("final_output"),
            "formatted_response": formatted
        })
    
    return JSONResponse({
        "has_error": True,
        "error_type": error_type,
        "error_message": error_msg,
        "auto_fixed": False,
        "reason": result.get("error", "No se pudo corregir automáticamente")
    })


@router.post("/quick")
async def quick_autofix(code: str = Form(...), language: str = Form("python")):
    """
    Ejecuta auto-fix rápido en un código.
    """
    from core.chat_autofix_integration import try_auto_fix
    
    result = await try_auto_fix(code, "", language)
    
    if result.get("success"):
        return JSONResponse({
            "success": True,
            "code_changed": result.get("code_changed"),
            "fixed_code": result.get("fixed_code"),
            "fixes_applied": result.get("fixes_applied"),
            "verified": result.get("verified"),
            "final_output": result.get("final_output")
        })
    
    return JSONResponse({
        "success": False,
        "error": result.get("error")
    })


@router.get("/status")
async def autofix_chat_status():
    """Estado de la integración auto-fix en chat"""
    return JSONResponse({
        "status": "active",
        "features": [
            "Detección automática de errores en respuestas",
            "Corrección automática con re-ejecución",
            "Integración con el flujo de chat"
        ]
    })
