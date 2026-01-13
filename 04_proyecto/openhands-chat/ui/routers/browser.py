"""
Router para Browser Screenshots (como OpenHands)

El Navegador en OpenHands muestra screenshots del browser que el agente controla.
Los screenshots se envían desde el agente vía WebSocket y se almacenan temporalmente.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import base64
from typing import Dict, Optional

router = APIRouter(prefix="/api/browser", tags=["browser"])

# Almacenamiento temporal de screenshots por conversación
# En producción, esto podría guardarse en la DB
browser_screenshots: Dict[int, dict] = {}


@router.get("/screenshot")
async def get_screenshot(conversation_id: int = None):
    """Obtener el último screenshot del navegador para una conversación"""
    if not conversation_id:
        return JSONResponse({"screenshot": None, "url": None})
    
    data = browser_screenshots.get(conversation_id, {})
    return JSONResponse({
        "screenshot": data.get("screenshot"),
        "url": data.get("url", "")
    })


@router.post("/screenshot")
async def save_screenshot(request: Request):
    """Guardar un screenshot del navegador (llamado desde el agente)"""
    try:
        data = await request.json()
        conversation_id = data.get("conversation_id")
        screenshot = data.get("screenshot")  # Base64
        url = data.get("url", "")
        
        if not conversation_id or not screenshot:
            return JSONResponse(
                {"status": "error", "message": "conversation_id y screenshot requeridos"},
                status_code=400
            )
        
        browser_screenshots[conversation_id] = {
            "screenshot": screenshot,
            "url": url
        }
        
        return JSONResponse({"status": "saved"})
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@router.delete("/screenshot")
async def clear_screenshot(conversation_id: int = None):
    """Limpiar screenshot de una conversación"""
    if conversation_id and conversation_id in browser_screenshots:
        del browser_screenshots[conversation_id]
    return JSONResponse({"status": "cleared"})


def update_screenshot(conversation_id: int, url: str, screenshot_base64: str):
    """Función helper para actualizar screenshot desde código Python"""
    browser_screenshots[conversation_id] = {
        "screenshot": screenshot_base64,
        "url": url
    }


def get_current_screenshot(conversation_id: int) -> Optional[dict]:
    """Función helper para obtener screenshot desde código Python"""
    return browser_screenshots.get(conversation_id)
