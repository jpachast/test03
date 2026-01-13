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
    
    repo_name = conv_data.get("repo_name", "") or conv_data.get("project_name", "")
    
    if is_main_project(repo_name):
        return JSONResponse({
            "error": "El editor de código no está disponible para el proyecto principal",
            "is_main_project": True
        }, status_code=403)
    
    workspace_path = conv_data.get("workspace_path")
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
    status = get_code_server_status()
    
    if status.get("status") != "running":
        return HTMLResponse(
            content="<h1>Code Server no está corriendo</h1><p>Inicia el editor desde el botón 'Código'</p>",
            status_code=503
        )
    
    port = status.get("port") or get_current_port()
    target_url = f"http://127.0.0.1:{port}/{path}"
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
