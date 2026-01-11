"""
Servidor web FastAPI
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from openhands.sdk import Conversation

from config.database import Database
from config.settings import Settings
from core.agent import create_agent
from core.workspace import setup_workspace, list_projects, get_project_info


# Inicializar
app = FastAPI(title="OpenHands Chat", version="1.0.0")
settings = Settings()
db = Database()

# Templates y static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent.parent / "static"

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Estado global
current_conversation = None
current_workspace = None


# === PÁGINAS ===

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal"""
    has_api_key = db.has_api_key()
    projects = list_projects(settings.projects_dir)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "has_api_key": has_api_key,
        "projects": projects,
        "current_workspace": current_workspace,
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Página de configuración"""
    current_settings = db.get_all_settings()
    has_api_key = db.has_api_key()
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": current_settings,
        "has_api_key": has_api_key,
        "default_model": settings.default_model,
    })


# === API ENDPOINTS ===

@app.post("/api/settings/api-key")
async def save_api_key(api_key: str = Form(...)):
    """Guardar API key"""
    if not api_key or len(api_key) < 10:
        raise HTTPException(status_code=400, detail="API key inválida")
    
    db.set_api_key(api_key)
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.post("/api/settings/model")
async def save_model(model: str = Form(...)):
    """Guardar modelo"""
    db.set_setting("llm_model", model)
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.post("/api/project/new")
async def create_project(name: str = Form(...)):
    """Crear nuevo proyecto"""
    global current_workspace
    
    try:
        workspace = setup_workspace(name, "nuevo", settings.projects_dir)
        current_workspace = workspace
        db.add_project(name, workspace)
        return RedirectResponse(url=f"/?project={name}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/project/clone")
async def clone_project(git_url: str = Form(...)):
    """Clonar proyecto de Git"""
    global current_workspace
    
    try:
        workspace = setup_workspace(git_url, "git", settings.projects_dir)
        name = Path(workspace).name
        current_workspace = workspace
        db.add_project(name, workspace, git_url)
        return RedirectResponse(url=f"/?project={name}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/project/select")
async def select_project(name: str = Form(...)):
    """Seleccionar proyecto existente"""
    global current_workspace
    
    try:
        workspace = setup_workspace(name, "existente", settings.projects_dir)
        current_workspace = workspace
        return RedirectResponse(url=f"/?project={name}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/project/info/{name}")
async def project_info(name: str):
    """Obtener info de un proyecto"""
    project_path = settings.projects_dir / name
    info = get_project_info(str(project_path))
    
    if info is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return JSONResponse(info)


# Variable global para capturar respuestas
last_agent_response = ""

def capture_response(event):
    """Callback para capturar la respuesta del agente"""
    global last_agent_response
    
    event_type = str(type(event).__name__)
    
    # Capturar de ActionEvent con FinishAction
    if event_type == 'ActionEvent':
        if hasattr(event, 'action') and event.action:
            action = event.action
            # Verificar si es FinishAction
            action_type = str(type(action).__name__)
            if 'Finish' in action_type:
                if hasattr(action, 'message') and action.message:
                    last_agent_response = action.message
                    print(f"[CALLBACK] Captured FINISH message: {action.message[:200]}...")
    
    # También capturar de MessageEvent
    elif event_type == 'MessageEvent':
        if hasattr(event, 'llm_message') and event.llm_message:
            msg = event.llm_message
            if hasattr(msg, 'role') and msg.role == 'assistant':
                if hasattr(msg, 'content') and msg.content:
                    text_parts = []
                    for part in msg.content:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        response = '\n'.join(text_parts)
                        print(f"[CALLBACK] Captured agent response: {response[:200]}...")
                        last_agent_response = response


@app.post("/api/chat/send")
async def send_message(message: str = Form(...), project: str = Form(None)):
    """Enviar mensaje al agente"""
    global current_conversation, current_workspace, last_agent_response
    
    # Resetear respuesta
    last_agent_response = ""
    
    # Verificar API key
    api_key = db.get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="API key no configurada")
    
    # Configurar workspace si no hay
    if current_workspace is None:
        if project:
            current_workspace = str(settings.projects_dir / project)
        else:
            current_workspace = str(settings.projects_dir)
    
    try:
        # Obtener o crear conversación en BD
        conversation_id = None
        if project:
            proj = db.get_project_by_name(project)
            if proj:
                conv = db.get_conversation(proj['id'])
                conversation_id = conv['id']
        
        # Guardar mensaje del usuario en BD
        if conversation_id:
            db.add_message(conversation_id, 'user', message)
        
        # SIEMPRE crear nueva conversación para cada mensaje 
        # (para asegurar que los callbacks se apliquen)
        model = db.get_setting("llm_model", settings.default_model)
        agent = create_agent(api_key, model)
        current_conversation = Conversation(
            agent=agent, 
            workspace=current_workspace,
            callbacks=[capture_response]
        )
        
        # Enviar mensaje
        current_conversation.send_message(message)
        
        # Ejecutar (esto puede tomar tiempo)
        await asyncio.to_thread(current_conversation.run)
        
        # Obtener la respuesta capturada
        agent_response = last_agent_response
        
        # Si no hay respuesta capturada, usar mensaje genérico
        if not agent_response:
            agent_response = "✅ Tarea completada. Revisa los archivos creados en tu proyecto."
        
        # Guardar respuesta del agente en BD
        if conversation_id:
            db.add_message(conversation_id, 'assistant', agent_response)
        
        return JSONResponse({
            "status": "ok",
            "message": agent_response,
            "user_message": message
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)


@app.post("/api/chat/reset")
async def reset_chat():
    """Resetear conversación"""
    global current_conversation
    current_conversation = None
    return JSONResponse({"status": "ok"})


@app.get("/api/chat/messages/{project_name}")
async def get_messages(project_name: str):
    """Obtener mensajes de un proyecto"""
    messages = db.get_messages_by_project(project_name)
    return JSONResponse({"messages": messages})


# === HEALTH CHECK ===

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "has_api_key": db.has_api_key()}
