"""
Router para gestionar el servidor de aplicaciones (App Viewer)
Port Forwarding dinámico como OpenHands Cloud
Incluye soporte para WebSockets (hot-reload, tiempo real)
"""
import os
import asyncio
import re
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
import httpx
import websockets

from config.settings import Settings
from config.database import Database
from core.app_server import (
    start_app_server,
    stop_app_server,
    get_app_server_status,
    get_active_port,
    set_forwarded_port,
    is_port_listening,
    APP_SERVER_INSTANCES,
    CONVERSATION_PORTS
)

router = APIRouter(prefix="/api/app-server", tags=["app-server"])
settings = Settings()
db = Database()


@router.get("/status")
async def get_status(conversation_id: int = None):
    """Obtener estado del servidor de app"""
    status = get_app_server_status(conversation_id)
    return JSONResponse(status)


@router.post("/start")
async def api_start_app_server(request: Request):
    """Inicia el servidor de app para una conversación"""
    data = await request.json()
    conv_id = data.get("conversation_id")
    
    if not conv_id:
        return JSONResponse({"status": "error", "message": "conversation_id requerido"}, status_code=400)
    
    # Obtener datos de la conversación
    conv_data = db.get_conversation(int(conv_id), by_conv_id=True)
    if not conv_data:
        return JSONResponse({"status": "error", "message": "Conversación no encontrada"}, status_code=404)
    
    workspace_path = conv_data.get("workspace_path")
    if not workspace_path or not os.path.isdir(workspace_path):
        return JSONResponse({"status": "error", "message": "Workspace no existe"}, status_code=404)
    
    result = start_app_server(workspace_path, int(conv_id))
    
    if result.get("status") in ["started", "running"]:
        port = result.get("port")
        result["url"] = f"/app-preview/"
        result["direct_port"] = port
    
    return JSONResponse(result)


@router.post("/prestart")
async def api_prestart_app_server(request: Request):
    """
    Pre-inicia el servidor de app en background cuando se carga el chat.
    Así cuando el usuario haga clic en el botón de navegador, ya estará listo.
    """
    import threading
    
    data = await request.json()
    conv_id = data.get("conversation_id")
    
    if not conv_id:
        return JSONResponse({"status": "skipped", "reason": "no conversation_id"})
    
    conv_data = db.get_conversation(int(conv_id), by_conv_id=True)
    if not conv_data:
        return JSONResponse({"status": "skipped", "reason": "conversation not found"})
    
    workspace_path = conv_data.get("workspace_path")
    if not workspace_path or not os.path.isdir(workspace_path):
        return JSONResponse({"status": "skipped", "reason": "no workspace"})
    
    # Iniciar en background
    def _start_bg():
        start_app_server(workspace_path, int(conv_id))
    
    thread = threading.Thread(target=_start_bg, daemon=True)
    thread.start()
    
    return JSONResponse({"status": "starting", "conversation_id": conv_id})


@router.post("/stop")
async def api_stop_app_server(request: Request):
    """Detiene el servidor de app"""
    data = await request.json()
    conv_id = data.get("conversation_id")
    
    if conv_id:
        result = stop_app_server(int(conv_id))
    else:
        result = {"status": "error", "message": "conversation_id requerido"}
    
    return JSONResponse(result)


# Endpoint para configurar puerto manualmente
@router.post("/set-port")
async def api_set_port(request: Request):
    """Configura el puerto para port forwarding"""
    data = await request.json()
    conv_id = data.get("conversation_id")
    port = data.get("port")
    
    if not conv_id or not port:
        return JSONResponse({"status": "error", "message": "conversation_id y port requeridos"}, status_code=400)
    
    result = set_forwarded_port(int(conv_id), int(port))
    return JSONResponse(result)


# Endpoint para obtener puerto activo
@router.get("/active-port")
async def api_get_active_port(conversation_id: int = None):
    """Obtiene el puerto activo detectado automáticamente"""
    if not conversation_id:
        return JSONResponse({"status": "error", "message": "conversation_id requerido"}, status_code=400)
    
    result = get_active_port(conversation_id)
    return JSONResponse(result)


# Proxy con Port Forwarding dinámico
@router.api_route("/app-preview/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
async def proxy_app_server(request: Request, path: str, conversation_id: int = None):
    """
    Proxy con Port Forwarding dinámico como OpenHands Cloud.
    Detecta automáticamente el puerto del servidor del agente.
    """
    # Si no viene conversation_id en query, intentar extraerlo del Referer
    # Esto es necesario para rutas relativas (css/styles.css sin ?conversation_id)
    if not conversation_id:
        referer = request.headers.get("referer", "")
        # Intentar extraer de query param en referer
        match = re.search(r'conversation_id=(\d+)', referer)
        if match:
            conversation_id = int(match.group(1))
        else:
            # Intentar extraer de URL /chat/ID
            match = re.search(r'/chat/(\d+)', referer)
            if match:
                conversation_id = int(match.group(1))
    
    if not conversation_id:
        return HTMLResponse(
            content="""
            <html>
            <head><style>
                body { background: #1e1e1e; color: #ccc; font-family: sans-serif; 
                       display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .msg { text-align: center; }
            </style></head>
            <body><div class="msg">
                <h2>🌐 Selecciona una conversación</h2>
                <p>Abre un chat para ver la aplicación.</p>
            </div></body>
            </html>
            """,
            status_code=400
        )
    
    # Obtener puerto activo (detectado automáticamente)
    port_info = get_active_port(conversation_id)
    
    # Verificar si hay servidor del agente activo
    # NO usar servidor de archivos estáticos como fallback (evita directory listing)
    if port_info.get("status") == "no_server" or not port_info.get("port"):
        return HTMLResponse(
            content=f"""
            <html>
            <head><style>
                body {{ background: #1e1e1e; color: #ccc; font-family: sans-serif; 
                       display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .msg {{ text-align: center; }}
                code {{ background: #333; padding: 2px 8px; border-radius: 4px; }}
                .ports {{ margin-top: 20px; font-size: 12px; color: #888; }}
            </style></head>
            <body><div class="msg">
                <h2>🚀 Esperando servidor...</h2>
                <p>El agente debe iniciar un servidor web.</p>
                <p>Puertos detectados automáticamente: <code>3000</code>, <code>5000</code>, <code>8000</code>, <code>8080</code></p>
                <div class="ports">
                    Conversación: {conversation_id}
                </div>
            </div></body>
            </html>
            """,
            status_code=503
        )
    
    port = port_info.get("port")
    
    target_url = f"http://127.0.0.1:{port}/{path}"
    
    # Filtrar conversation_id del query string
    query_params = {k: v for k, v in request.query_params.items() if k != 'conversation_id'}
    if query_params:
        target_url += f"?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = dict(request.headers)
            headers.pop("host", None)
            headers.pop("accept-encoding", None)
            
            body = await request.body()
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body if body else None,
                follow_redirects=False
            )
            
            response_headers = dict(response.headers)
            response_headers.pop("transfer-encoding", None)
            response_headers.pop("content-encoding", None)
            response_headers.pop("content-length", None)  # Remover para recalcular
            
            content = response.content
            content_type = response_headers.get("content-type", "")
            
            # Reescribir rutas en HTML para que pasen por el proxy
            # Esto es similar a cómo Daytona/OpenHands mapea URLs
            if "text/html" in content_type:
                content_str = content.decode("utf-8", errors="ignore")
                base_path = f"/api/app-server/app-preview"
                
                # 1. Reescribir src="/..." y href="/..." (rutas absolutas)
                content_str = re.sub(
                    r'(src|href)=["\']/((?!/)(?!http)[^"\']+)["\']',
                    rf'\1="{base_path}/\2?conversation_id={conversation_id}"',
                    content_str
                )
                
                # 2. Reescribir action="/..." en formularios
                content_str = re.sub(
                    r'action=["\']/((?!/)(?!http)[^"\']+)["\']',
                    rf'action="{base_path}/\1?conversation_id={conversation_id}"',
                    content_str
                )
                
                # 3. Reescribir url("/...") en estilos inline (para backgrounds, fonts)
                content_str = re.sub(
                    r'url\(["\']?/((?!/)(?!http)[^"\')\s]+)["\']?\)',
                    rf'url("{base_path}/\1?conversation_id={conversation_id}")',
                    content_str
                )
                
                # 4. Agregar <base> tag para rutas relativas si no existe
                if '<base' not in content_str.lower():
                    content_str = re.sub(
                        r'(<head[^>]*>)',
                        rf'\1<base href="{base_path}/?conversation_id={conversation_id}">',
                        content_str,
                        count=1,
                        flags=re.IGNORECASE
                    )
                
                # 5. Reescribir WebSocket URLs (ws://localhost:PORT -> wss://host/api/app-server/app-preview-ws)
                # Esto permite hot-reload y tiempo real
                ws_base = f"/api/app-server/app-preview-ws"
                content_str = re.sub(
                    r'(["\'])ws://localhost:\d+(/[^"\']*)?(["\'])',
                    rf'\1wss://" + window.location.host + "{ws_base}\2?conversation_id={conversation_id}\3',
                    content_str
                )
                content_str = re.sub(
                    r'(["\'])ws://127\.0\.0\.1:\d+(/[^"\']*)?(["\'])',
                    rf'\1wss://" + window.location.host + "{ws_base}\2?conversation_id={conversation_id}\3',
                    content_str
                )
                
                content = content_str.encode("utf-8")
            
            # También reescribir URLs en CSS
            elif "text/css" in content_type:
                content_str = content.decode("utf-8", errors="ignore")
                base_path = f"/api/app-server/app-preview"
                
                # Reescribir url("/...") y url('/...') y url(/...)
                content_str = re.sub(
                    r'url\(["\']?/((?!/)(?!http|data:)[^"\')\s]+)["\']?\)',
                    rf'url("{base_path}/\1?conversation_id={conversation_id}")',
                    content_str
                )
                content = content_str.encode("utf-8")
            
            return HTMLResponse(
                content=content,
                status_code=response.status_code,
                headers=response_headers
            )
    except httpx.ConnectError:
        return HTMLResponse(
            content=f"""
            <html>
            <head><style>
                body {{ background: #1e1e1e; color: #ccc; font-family: sans-serif; 
                       display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .msg {{ text-align: center; }}
                code {{ background: #333; padding: 2px 8px; border-radius: 4px; }}
            </style></head>
            <body><div class="msg">
                <h2>⏳ Conectando al puerto {port}...</h2>
                <p>El servidor está iniciando. Recarga en unos segundos.</p>
            </div></body>
            </html>
            """,
            status_code=503
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error de conexión</h1><p>{str(e)}</p><p>Puerto: {port}</p>",
            status_code=502
        )


# Mantener compatibilidad con el endpoint antiguo
@router.post("/ensure")
async def ensure_running(request: Request):
    """Compatibilidad: asegura que hay un servidor corriendo"""
    return await api_start_app_server(request)


# ============================================================================
# WebSocket Proxy - Para hot-reload, tiempo real, etc.
# ============================================================================

@router.websocket("/app-preview-ws/{path:path}")
async def websocket_proxy(websocket: WebSocket, path: str):
    """
    Proxy WebSocket para apps con tiempo real (hot-reload, chat, etc.)
    Similar a cómo Daytona/OpenHands maneja WebSockets
    """
    await websocket.accept()
    
    # Extraer conversation_id de query params
    conversation_id = websocket.query_params.get("conversation_id")
    if not conversation_id:
        await websocket.close(code=4000, reason="conversation_id requerido")
        return
    
    try:
        conversation_id = int(conversation_id)
    except ValueError:
        await websocket.close(code=4001, reason="conversation_id inválido")
        return
    
    # Obtener puerto activo
    port_info = get_active_port(conversation_id)
    if port_info.get("status") == "no_server" or not port_info.get("port"):
        await websocket.close(code=4002, reason="No hay servidor activo")
        return
    
    port = port_info.get("port")
    
    # Construir URL del WebSocket del servidor del agente
    ws_url = f"ws://127.0.0.1:{port}/{path}"
    query_params = {k: v for k, v in websocket.query_params.items() if k != 'conversation_id'}
    if query_params:
        ws_url += f"?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
    
    try:
        # Conectar al WebSocket del servidor del agente
        async with websockets.connect(ws_url) as agent_ws:
            
            async def forward_to_agent():
                """Reenviar mensajes del cliente al servidor del agente"""
                try:
                    while True:
                        data = await websocket.receive()
                        if data["type"] == "websocket.receive":
                            if "text" in data:
                                await agent_ws.send(data["text"])
                            elif "bytes" in data:
                                await agent_ws.send(data["bytes"])
                        elif data["type"] == "websocket.disconnect":
                            break
                except WebSocketDisconnect:
                    pass
                except Exception:
                    pass
            
            async def forward_to_client():
                """Reenviar mensajes del servidor del agente al cliente"""
                try:
                    async for message in agent_ws:
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except Exception:
                    pass
            
            # Ejecutar ambas direcciones en paralelo
            await asyncio.gather(
                forward_to_agent(),
                forward_to_client(),
                return_exceptions=True
            )
    
    except websockets.exceptions.ConnectionClosed:
        pass
    except ConnectionRefusedError:
        await websocket.close(code=4003, reason=f"No se puede conectar al puerto {port}")
    except Exception as e:
        await websocket.close(code=4004, reason=str(e)[:100])
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
