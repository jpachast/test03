"""
Stream Endpoints - API para streaming en tiempo real.

Endpoints:
    POST /api/stream/chat - Chat con streaming real token por token
    POST /api/stream/cancel - Cancelar un stream activo
    GET  /api/stream/status - Estado del streaming
"""

import json
import uuid
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stream", tags=["stream"])


@router.post("/chat")
async def stream_chat(request: Request):
    """
    Chat con streaming real token por token.
    
    Envía tokens via SSE conforme el LLM los genera.
    """
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        conversation_id = data.get("conversation_id")
        
        if not message:
            return JSONResponse({
                "success": False,
                "error": "Message required"
            }, status_code=400)
        
        # Generar ID único para este stream
        stream_id = str(uuid.uuid4())[:8]
        
        async def generate():
            """Generador SSE"""
            try:
                from core.realtime_stream import stream_response
                from config.database import Database
                
                db = Database()
                model = db.get_setting('llm_model', 'anthropic/claude-sonnet-4-20250514')
                api_key = db.get_llm_api_key()
                
                # Obtener historial si hay conversation_id
                conversation_history = []
                if conversation_id:
                    messages = db.get_messages(int(conversation_id))
                    # Últimos 10 mensajes
                    for msg in messages[-10:]:
                        conversation_history.append({
                            "role": msg["role"],
                            "content": msg["content"][:1000]  # Truncar
                        })
                
                # Enviar inicio
                yield f"data: {json.dumps({'type': 'start', 'stream_id': stream_id})}\n\n"
                
                full_response = ""
                
                async for event in stream_response(
                    message=message,
                    model=model,
                    api_key=api_key,
                    conversation_history=conversation_history
                ):
                    if event["type"] == "token":
                        full_response += event["content"]
                        yield f"data: {json.dumps(event)}\n\n"
                    elif event["type"] == "done":
                        # Guardar mensaje en BD
                        if conversation_id:
                            db.add_message(int(conversation_id), "user", message)
                            db.add_message(int(conversation_id), "assistant", full_response)
                        yield f"data: {json.dumps(event)}\n\n"
                    elif event["type"] == "error":
                        yield f"data: {json.dumps(event)}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Stream chat error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/quick")
async def quick_stream(request: Request):
    """
    Stream rápido sin guardar en BD.
    
    Para respuestas simples que no necesitan persistencia.
    """
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        
        if not message:
            return JSONResponse({
                "success": False,
                "error": "Message required"
            }, status_code=400)
        
        async def generate():
            try:
                from core.realtime_stream import stream_response
                from config.database import Database
                
                db = Database()
                model = db.get_setting('llm_model', 'anthropic/claude-sonnet-4-20250514')
                api_key = db.get_llm_api_key()
                
                async for event in stream_response(
                    message=message,
                    model=model,
                    api_key=api_key
                ):
                    yield f"data: {json.dumps(event)}\n\n"
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/status")
async def stream_status():
    """Estado del sistema de streaming"""
    return JSONResponse({
        "success": True,
        "status": "active",
        "features": {
            "realtime_tokens": True,
            "sse_events": True,
            "cancel_support": True
        }
    })


@router.get("/test")
async def test_stream():
    """
    Test de streaming - envía tokens de prueba.
    """
    async def generate():
        test_message = "Hola, este es un test de streaming token por token. Cada palabra aparece gradualmente."
        
        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        
        for word in test_message.split():
            yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
            await asyncio.sleep(0.1)  # Simular delay del LLM
        
        yield f"data: {json.dumps({'type': 'done', 'content': test_message})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
