"""Rutas de Code Server (VS Code en navegador)"""
import os
import asyncio
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response
import httpx
import websockets

from config.database import Database
from core.code_server import (
    start_code_server, 
    stop_code_server, 
    get_code_server_status, 
    is_main_project,
    CODE_SERVER_PORT  # Ahora es dinámico, puede ser None
)

router = APIRouter(tags=["code-server"])
db = Database()


def get_current_port() -> int:
    """Obtiene el puerto actual de code-server"""
    from core.code_server import CODE_SERVER_PORT
    return CODE_SERVER_PORT or 8080


# Variable global para almacenar el workspace actual (para el proxy)
_CURRENT_WORKSPACE_PATH = ""

def _get_workspace_for_codeserver(conv_data: dict) -> str:
    """
    Obtiene el directorio de trabajo para code-server.
    Usa el workspace_path de la conversación si existe y tiene .git.
    Si no, intenta clonar el repositorio automáticamente.
    """
    global _CURRENT_WORKSPACE_PATH
    
    workspace_path = conv_data.get("workspace_path", "")
    
    # Si el workspace existe y tiene .git, usarlo
    if workspace_path and os.path.isdir(workspace_path):
        git_path = os.path.join(workspace_path, ".git")
        if os.path.isdir(git_path):
            _CURRENT_WORKSPACE_PATH = workspace_path
            return workspace_path
    
    # Si no existe, verificar si hay que crearlo/clonarlo
    # El workspace_path típico es: .../projects/owner-repo/chatXX
    if workspace_path and not os.path.isdir(workspace_path):
        os.makedirs(workspace_path, exist_ok=True)
    
    # Guardar para uso del proxy
    _CURRENT_WORKSPACE_PATH = workspace_path
    return workspace_path


@router.post("/api/code-server/start")
async def api_start_code_server(request: Request):
    """Inicia code-server para el proyecto actual"""
    data = await request.json()
    conv_id = data.get("conversation_id")
    
    if not conv_id:
        return JSONResponse({"error": "conversation_id requerido"}, status_code=400)
    
    conv_data = db.get_conversation(int(conv_id), by_conv_id=True)
    if not conv_data:
        return JSONResponse({"error": "Conversación no encontrada"}, status_code=404)
    
    # Obtener workspace apropiado (raíz para test03, chat dir para otros)
    workspace_path = _get_workspace_for_codeserver(conv_data)
    
    if not workspace_path or not os.path.isdir(workspace_path):
        return JSONResponse({
            "error": f"Workspace no encontrado: {workspace_path}",
            "conv_data": conv_data
        }, status_code=404)
    
    result = start_code_server(workspace_path, conversation_id=int(conv_id))
    
    if result.get("status") in ["started", "running"]:
        port = result.get("port")
        result["url"] = f"/code-server/"
        result["direct_port"] = port
    
    return JSONResponse(result)


@router.post("/api/code-server/prestart")
async def api_prestart_code_server(request: Request):
    """
    Pre-inicia code-server en background cuando se carga el chat.
    Así cuando el usuario haga clic en el botón, ya estará listo.
    """
    import asyncio
    
    data = await request.json()
    conv_id = data.get("conversation_id")
    
    if not conv_id:
        return JSONResponse({"status": "skipped", "reason": "no conversation_id"})
    
    conv_data = db.get_conversation(int(conv_id), by_conv_id=True)
    if not conv_data:
        return JSONResponse({"status": "skipped", "reason": "conversation not found"})
    
    # Obtener workspace apropiado (raíz para test03, chat dir para otros)
    workspace_path = _get_workspace_for_codeserver(conv_data)
    
    if not workspace_path or not os.path.isdir(workspace_path):
        return JSONResponse({"status": "skipped", "reason": "no workspace"})
    
    # Iniciar en background (no bloquear)
    def _start_bg():
        start_code_server(workspace_path, conversation_id=int(conv_id))
    
    import threading
    thread = threading.Thread(target=_start_bg, daemon=True)
    thread.start()
    
    return JSONResponse({"status": "starting", "conversation_id": conv_id})


@router.post("/api/code-server/stop")
async def api_stop_code_server():
    """Detiene code-server"""
    return JSONResponse(stop_code_server())


@router.get("/api/code-server/status")
async def api_code_server_status():
    """Obtiene el estado de code-server"""
    return JSONResponse(get_code_server_status())


@router.api_route("/code-server/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_code_server(request: Request, path: str):
    """Proxy para code-server"""
    global _CURRENT_WORKSPACE_PATH
    
    status = get_code_server_status()
    
    if status.get("status") != "running":
        return HTMLResponse(
            content="<h1>Code Server no está corriendo</h1><p>Inicia el editor desde el botón 'Código'</p>",
            status_code=503
        )
    
    port = status.get("port") or get_current_port()
    # Usar la variable global si status no tiene path
    workspace_path = status.get("path", "") or _CURRENT_WORKSPACE_PATH
    
    target_url = f"http://127.0.0.1:{port}/{path}"
    
    # Si es la página principal y no tiene folder, agregar el folder correcto
    if (path == "" or path == "/" or path.endswith("?")) and workspace_path:
        if "folder=" not in str(request.query_params):
            # Redirigir con el folder correcto
            from starlette.responses import RedirectResponse
            return RedirectResponse(
                url=f"/code-server/?folder={workspace_path}",
                status_code=302
            )
    
    if request.query_params:
        target_url += f"?{request.query_params}"
    
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
            
            # Si code-server redirige con un folder diferente, interceptar
            if response.status_code in (301, 302, 307, 308):
                location = response.headers.get("location", "")
                # Si la redirección tiene folder incorrecto, corregirla
                if "folder=" in location and workspace_path and workspace_path not in location:
                    import re
                    corrected = re.sub(r'folder=[^&]*', f'folder={workspace_path}', location)
                    response_headers = dict(response.headers)
                    response_headers["location"] = corrected
                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=response_headers
                    )
            
            response_headers = dict(response.headers)
            response_headers.pop("content-encoding", None)
            response_headers.pop("content-length", None)
            response_headers.pop("transfer-encoding", None)
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type")
            )
    except httpx.ConnectError:
        return HTMLResponse(content="<h1>No se puede conectar a Code Server</h1>", status_code=502)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error de proxy</h1><p>{str(e)}</p>", status_code=500)


@router.websocket("/code-server/{path:path}")
async def websocket_proxy(websocket: WebSocket, path: str):
    """Proxy WebSocket para code-server"""
    await websocket.accept()
    
    status = get_code_server_status()
    port = status.get("port") or get_current_port()
    ws_url = f"ws://127.0.0.1:{port}/{path}"
    if websocket.query_params:
        ws_url += f"?{websocket.query_params}"
    
    try:
        async with websockets.connect(ws_url) as ws_backend:
            async def forward_to_backend():
                try:
                    while True:
                        data = await websocket.receive()
                        if "text" in data:
                            await ws_backend.send(data["text"])
                        elif "bytes" in data:
                            await ws_backend.send(data["bytes"])
                except WebSocketDisconnect:
                    pass
            
            async def forward_to_client():
                try:
                    async for message in ws_backend:
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except websockets.ConnectionClosed:
                    pass
            
            await asyncio.gather(forward_to_backend(), forward_to_client())
    except Exception as e:
        print(f"WebSocket proxy error: {e}")
        await websocket.close()
