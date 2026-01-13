"""
Router para gestionar el servidor de aplicaciones (App Viewer)
Implementación idéntica a OpenHands con puertos dinámicos por conversación
"""
import os
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
import httpx

from config.settings import Settings
from config.database import Database
from core.app_server import (
    start_app_server,
    stop_app_server,
    get_app_server_status,
    APP_SERVER_INSTANCES
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


# Proxy para el servidor de app
@router.api_route("/app-preview/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
async def proxy_app_server(request: Request, path: str, conversation_id: int = None):
    """Proxy para el servidor de aplicaciones"""
    # Obtener el puerto del servidor para esta conversación específica
    status = get_app_server_status(conversation_id)
    
    if status.get("status") != "running":
        return HTMLResponse(
            content="""
            <html>
            <head><style>
                body { background: #1e1e1e; color: #ccc; font-family: sans-serif; 
                       display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .msg { text-align: center; }
            </style></head>
            <body><div class="msg">
                <h2>🌐 Servidor no iniciado</h2>
                <p>El servidor de aplicaciones se iniciará automáticamente cuando abras un proyecto.</p>
            </div></body>
            </html>
            """,
            status_code=503
        )
    
    port = status.get("port")
    target_url = f"http://127.0.0.1:{port}/{path}"
    # Filtrar conversation_id del query string (no enviarlo al servidor de archivos)
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
            
            return HTMLResponse(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers
            )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error de conexión</h1><p>{str(e)}</p>",
            status_code=502
        )


# Mantener compatibilidad con el endpoint antiguo
@router.post("/ensure")
async def ensure_running(request: Request):
    """Compatibilidad: asegura que hay un servidor corriendo"""
    return await api_start_app_server(request)
