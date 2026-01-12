"""
Servidor web FastAPI con streaming SSE
"""

import os
import json
import asyncio
import queue
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from openhands.sdk import Conversation

from config.database import Database
from config.settings import Settings
from core.agent import create_agent
from core.workspace import setup_workspace, list_projects, get_project_info
from core.github_service import GitHubService


# Inicializar
app = FastAPI(title="OpenHands Chat", version="2.0.0")
settings = Settings()
db = Database()
github_service = GitHubService()

# Templates y static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent.parent / "static"
projects_dir = Path(__file__).parent.parent / "projects"

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Montar proyectos para servir archivos estáticos (si existe el directorio)
if projects_dir.exists():
    app.mount("/projects", StaticFiles(directory=str(projects_dir), html=True), name="projects")

# Estado global
current_conversation = None
current_workspace = None


# === MODELOS PYDANTIC ===

class GitHubTokenRequest(BaseModel):
    token: str

class LaunchRepoRequest(BaseModel):
    owner: str
    repo: str
    branch: str = "main"

class NewConversationRequest(BaseModel):
    project_id: int = None
    title: str = "Nueva conversación"


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


@app.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request):
    """Página de lista de conversaciones"""
    return templates.TemplateResponse("conversations.html", {"request": request})


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


# Variables globales para streaming
last_agent_response = ""
event_queue = None  # Cola para eventos SSE

def create_streaming_callback(q):
    """Crea un callback que envía eventos a la cola SSE"""
    def streaming_callback(event):
        global last_agent_response
        event_type = str(type(event).__name__)
        
        try:
            # ActionEvent - comandos y acciones
            if event_type == 'ActionEvent':
                if hasattr(event, 'action') and event.action:
                    action = event.action
                    action_type = str(type(action).__name__)
                    
                    # Terminal/Command
                    if 'Command' in action_type or 'Bash' in action_type:
                        cmd = getattr(action, 'command', '') or getattr(action, 'code', '')
                        if cmd:
                            q.put({"type": "action", "icon": "🔧", "text": f"Ejecutando: {cmd[:100]}"})
                    
                    # FileEditor - crear/editar archivos
                    elif 'File' in action_type or 'Edit' in action_type or 'Create' in action_type:
                        path = getattr(action, 'path', '') or getattr(action, 'file', '')
                        if path:
                            filename = Path(path).name if path else 'archivo'
                            q.put({"type": "action", "icon": "📄", "text": f"Editando: {filename}"})
                    
                    # Finish - respuesta final
                    elif 'Finish' in action_type:
                        if hasattr(action, 'message') and action.message:
                            last_agent_response = action.message
                            q.put({"type": "finish", "icon": "✅", "text": "Completado"})
                    
                    # Thinking/Planning
                    elif 'Think' in action_type or 'Message' in action_type:
                        msg = getattr(action, 'message', '') or getattr(action, 'thought', '')
                        if msg:
                            q.put({"type": "thinking", "icon": "💭", "text": msg[:150]})
            
            # ObservationEvent - resultados
            elif event_type == 'ObservationEvent':
                if hasattr(event, 'observation') and event.observation:
                    obs = event.observation
                    obs_type = str(type(obs).__name__)
                    
                    if 'Command' in obs_type or 'Bash' in obs_type:
                        output = getattr(obs, 'output', '') or getattr(obs, 'content', '')
                        if output and len(output) > 0:
                            preview = output[:100].replace('\n', ' ')
                            q.put({"type": "output", "icon": "📋", "text": f"Resultado: {preview}"})
            
            # MessageEvent - mensajes del agente
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
                                last_agent_response = response
                                # Solo enviar preview
                                q.put({"type": "thinking", "icon": "💭", "text": response[:100]})
        
        except Exception as e:
            print(f"[CALLBACK ERROR] {e}")
    
    return streaming_callback


def capture_response(event):
    """Callback legacy para capturar la respuesta del agente"""
    global last_agent_response
    
    event_type = str(type(event).__name__)
    
    if event_type == 'ActionEvent':
        if hasattr(event, 'action') and event.action:
            action = event.action
            action_type = str(type(action).__name__)
            if 'Finish' in action_type:
                if hasattr(action, 'message') and action.message:
                    last_agent_response = action.message
    
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
                        last_agent_response = '\n'.join(text_parts)


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


@app.post("/api/chat/stream")
async def stream_message(message: str = Form(...), project: str = Form(None)):
    """Enviar mensaje al agente con streaming SSE"""
    global current_conversation, current_workspace, last_agent_response
    
    # Resetear respuesta
    last_agent_response = ""
    
    # Verificar API key
    api_key = db.get_api_key()
    if not api_key:
        return JSONResponse({"error": "API key no configurada"}, status_code=400)
    
    # SIEMPRE usar el workspace del proyecto actual
    if project:
        workspace = str(settings.projects_dir / project)
    else:
        workspace = str(settings.projects_dir)
    current_workspace = workspace
    
    print(f"[STREAM] Workspace: {workspace}")
    
    async def generate_events():
        global last_agent_response
        q = queue.Queue()
        
        # Obtener conversación ID para guardar
        conversation_id = None
        if project:
            proj = db.get_project_by_name(project)
            if proj:
                conv = db.get_conversation(proj['id'])
                conversation_id = conv['id']
        
        # Guardar mensaje del usuario
        if conversation_id:
            db.add_message(conversation_id, 'user', message)
        
        # Evento inicial
        yield f"data: {json.dumps({'type': 'start', 'icon': '🚀', 'text': 'Iniciando...'})}\n\n"
        
        # Crear agente con callback de streaming
        model = db.get_setting("llm_model", settings.default_model)
        agent = create_agent(api_key, model)
        
        streaming_cb = create_streaming_callback(q)
        conv = Conversation(
            agent=agent,
            workspace=workspace,
            callbacks=[streaming_cb, capture_response]
        )
        
        # Enviar mensaje
        conv.send_message(message)
        
        # Ejecutar en thread separado
        def run_agent():
            try:
                conv.run()
            except Exception as e:
                q.put({"type": "error", "icon": "❌", "text": str(e)})
            finally:
                q.put(None)  # Señal de fin
        
        thread = threading.Thread(target=run_agent)
        thread.start()
        
        # Enviar eventos mientras el agente trabaja
        while True:
            try:
                event = q.get(timeout=0.5)
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                # Enviar heartbeat para mantener conexión
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        thread.join(timeout=5)
        
        # Enviar respuesta final
        agent_response = last_agent_response
        if not agent_response:
            agent_response = "✅ Tarea completada. Revisa los archivos creados."
        
        # Guardar respuesta
        if conversation_id:
            db.add_message(conversation_id, 'assistant', agent_response)
        
        yield f"data: {json.dumps({'type': 'done', 'message': agent_response})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


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


# === GITHUB ENDPOINTS ===

@app.get("/api/github/status")
async def github_status():
    """Estado de la configuración de GitHub"""
    has_token = db.has_github_token()
    username = db.get_github_username() if has_token else None
    return {
        "configured": has_token,
        "username": username
    }


@app.post("/api/github/token")
async def save_github_token(request: GitHubTokenRequest):
    """Guardar y validar token de GitHub"""
    github_service.set_token(request.token)
    result = github_service.validate_token()
    
    if result.get("valid"):
        db.set_github_token(request.token)
        db.set_github_username(result.get("username", ""))
        return {
            "success": True,
            "username": result.get("username"),
            "name": result.get("name"),
            "avatar_url": result.get("avatar_url")
        }
    else:
        return JSONResponse({
            "success": False,
            "error": result.get("error", "Token inválido")
        }, status_code=400)


@app.delete("/api/github/token")
async def delete_github_token():
    """Eliminar token de GitHub"""
    db.delete_setting("github_token")
    db.delete_setting("github_username")
    github_service.set_token(None)
    return {"success": True}


@app.get("/api/github/repos")
async def get_github_repos(page: int = 1, per_page: int = 30):
    """Obtener repositorios del usuario"""
    token = db.get_github_token()
    if not token:
        raise HTTPException(status_code=401, detail="GitHub no configurado")
    
    github_service.set_token(token)
    result = github_service.get_user_repos(page, per_page)
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))


@app.get("/api/github/repos/{owner}/{repo}/branches")
async def get_repo_branches(owner: str, repo: str):
    """Obtener branches de un repositorio"""
    token = db.get_github_token()
    if not token:
        raise HTTPException(status_code=401, detail="GitHub no configurado")
    
    github_service.set_token(token)
    result = github_service.get_repo_branches(owner, repo)
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))


@app.post("/api/github/launch")
async def launch_repo(request: LaunchRepoRequest):
    """Iniciar/clonar un repositorio y crear conversación"""
    global current_workspace
    
    token = db.get_github_token()
    if not token:
        raise HTTPException(status_code=401, detail="GitHub no configurado")
    
    github_service.set_token(token)
    
    # Caso especial: si es el repositorio del proyecto principal (test03)
    is_main_project = (request.owner == "jpachast" and request.repo == "test03")
    
    # Estructura: projects/{owner}-{repo}/chat{id}/
    repo_folder = f"{request.owner}-{request.repo}"
    repo_base_path = settings.projects_dir / repo_folder
    repo_base_path.mkdir(parents=True, exist_ok=True)
    
    # Contar chats existentes para este repo
    existing_chats = list(repo_base_path.glob("chat*"))
    chat_num = len(existing_chats) + 1
    chat_folder = f"chat{chat_num:02d}"
    
    # Path para este chat específico
    chat_path = repo_base_path / chat_folder
    
    if is_main_project:
        # Para test03: crear carpeta pero NO clonar
        chat_path.mkdir(parents=True, exist_ok=True)
        action = "created"
    else:
        # Para otros repos: clonar en la carpeta del chat
        clone_result = github_service.clone_repo(
            request.owner, request.repo, request.branch,
            str(chat_path)
        )
        
        if not clone_result.get("success"):
            raise HTTPException(status_code=500, detail=clone_result.get("error"))
        
        action = "cloned"
    
    # Guardar proyecto en BD (con path del chat específico)
    git_url = f"https://github.com/{request.owner}/{request.repo}.git"
    project_id = db.add_project_with_repo(
        name=f"{repo_folder}/{chat_folder}",
        path=str(chat_path),
        repo_owner=request.owner,
        repo_name=request.repo,
        branch=request.branch,
        git_url=git_url
    )
    
    # Crear conversación
    conv_id = db.create_conversation(project_id, f"Trabajo en {request.repo}")
    
    # Actualizar workspace actual
    current_workspace = str(chat_path)
    
    return {
        "success": True,
        "project_id": project_id,
        "conversation_id": conv_id,
        "project_name": f"{repo_folder}/{chat_folder}",
        "path": str(chat_path),
        "action": action
    }


# === CONVERSACIONES ENDPOINTS ===

@app.get("/api/conversations")
async def get_conversations(limit: int = 50):
    """Obtener todas las conversaciones recientes"""
    conversations = db.get_all_conversations(limit)
    return {"conversations": conversations}


@app.post("/api/conversations")
async def create_conversation(request: NewConversationRequest):
    """Crear nueva conversación"""
    conv_id = db.create_conversation(request.project_id, request.title)
    return {"success": True, "conversation_id": conv_id}


@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: int):
    """Obtener una conversación con sus mensajes y establecer workspace"""
    global current_workspace
    
    # Obtener conversación
    conversations = db.get_all_conversations()
    conv = next((c for c in conversations if c['id'] == conv_id), None)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    # Obtener el proyecto para establecer el workspace
    project = db.get_project(conv['project_id'])
    if project and project.get('path'):
        current_workspace = project['path']
    
    # Obtener mensajes
    messages = db.get_messages(conv_id)
    
    return {
        "conversation": conv,
        "messages": messages,
        "workspace": current_workspace
    }


@app.put("/api/conversations/{conv_id}")
async def update_conversation_endpoint(conv_id: int, request: dict = None):
    """Actualizar conversación"""
    title = request.get('title') if request else None
    status = request.get('status') if request else None
    db.update_conversation(conv_id, title, status)
    return {"success": True}


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation_endpoint(conv_id: int):
    """Eliminar conversación y su carpeta"""
    import shutil
    
    # Obtener info de la conversación
    conversations = db.get_all_conversations()
    conv = next((c for c in conversations if c['id'] == conv_id), None)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    # Obtener proyecto para saber la carpeta
    project = db.get_project(conv['project_id'])
    
    if project and project.get('path'):
        # Eliminar carpeta física
        project_path = Path(project['path'])
        if project_path.exists():
            shutil.rmtree(project_path)
    
    # Eliminar de la BD
    db.delete_conversation(conv_id)
    if project:
        db.delete_project(conv['project_id'])
    
    return {"success": True}


@app.get("/api/conversations/project/{project_id}")
async def get_project_conversations(project_id: int):
    """Obtener conversaciones de un proyecto"""
    conversations = db.get_conversations_by_project(project_id)
    return {"conversations": conversations}


# === GIT OPERATIONS ===

class GitPullRequest(BaseModel):
    project: str
    owner: str
    repo: str
    branch: str = "main"

class GitPushRequest(BaseModel):
    project: str
    owner: str
    repo: str
    branch: str = "main"
    commit_message: str = "Actualización desde OpenHands Chat"

class GitPRRequest(BaseModel):
    project: str
    owner: str
    repo: str
    branch: str = "main"
    title: str
    body: str = ""


@app.post("/api/git/pull")
async def git_pull(request: GitPullRequest):
    """Hacer git pull en el proyecto"""
    import subprocess
    
    # Obtener path del proyecto
    project_path = settings.projects_dir / request.project
    
    if not project_path.exists():
        return {"success": False, "error": "Proyecto no encontrado"}
    
    try:
        # Ejecutar git pull
        result = subprocess.run(
            ["git", "pull", "origin", request.branch],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {"success": True, "message": result.stdout or "Pull exitoso"}
        else:
            return {"success": False, "error": result.stderr or "Error en pull"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout en operación"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/git/push")
async def git_push(request: GitPushRequest):
    """Hacer git add, commit y push"""
    import subprocess
    
    project_path = settings.projects_dir / request.project
    
    if not project_path.exists():
        return {"success": False, "error": "Proyecto no encontrado"}
    
    token = db.get_github_token()
    if not token:
        return {"success": False, "error": "GitHub no configurado"}
    
    username = db.get_github_username() or "openhands"
    
    try:
        # Configurar git user
        subprocess.run(
            ["git", "config", "user.email", f"{username}@users.noreply.github.com"],
            cwd=str(project_path), check=True
        )
        subprocess.run(
            ["git", "config", "user.name", username],
            cwd=str(project_path), check=True
        )
        
        # Git add
        subprocess.run(["git", "add", "-A"], cwd=str(project_path), check=True)
        
        # Git commit
        result = subprocess.run(
            ["git", "commit", "-m", request.commit_message],
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and "nothing to commit" in (result.stdout + result.stderr):
            return {"success": False, "error": "No hay cambios para commitear"}
        
        # Configurar remote con token
        remote_url = f"https://{token}@github.com/{request.owner}/{request.repo}.git"
        subprocess.run(
            ["git", "remote", "set-url", "origin", remote_url],
            cwd=str(project_path),
            check=True
        )
        
        # Git push
        result = subprocess.run(
            ["git", "push", "origin", request.branch],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "Push exitoso"}
        else:
            return {"success": False, "error": result.stderr or "Error en push"}
            
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/git/create-pr")
async def git_create_pr(request: GitPRRequest):
    """Crear Pull Request en GitHub"""
    token = db.get_github_token()
    if not token:
        return {"success": False, "error": "GitHub no configurado"}
    
    github_service.set_token(token)
    
    try:
        # Obtener branch default del repo
        import requests
        headers = {"Authorization": f"token {token}"}
        repo_info = requests.get(
            f"https://api.github.com/repos/{request.owner}/{request.repo}",
            headers=headers
        ).json()
        
        default_branch = repo_info.get("default_branch", "main")
        
        # Crear PR
        pr_data = {
            "title": request.title,
            "body": request.body,
            "head": request.branch,
            "base": default_branch
        }
        
        response = requests.post(
            f"https://api.github.com/repos/{request.owner}/{request.repo}/pulls",
            headers=headers,
            json=pr_data
        )
        
        if response.status_code == 201:
            pr = response.json()
            return {"success": True, "url": pr["html_url"], "number": pr["number"]}
        else:
            error_msg = response.json().get("message", "Error creando PR")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


# === HEALTH CHECK ===

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "has_api_key": db.has_api_key(),
        "has_github": db.has_github_token()
    }
