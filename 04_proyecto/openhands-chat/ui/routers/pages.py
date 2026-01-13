"""Rutas de páginas HTML"""
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config.database import Database
from config.settings import Settings
from core.workspace import list_projects

router = APIRouter(tags=["pages"])
settings = Settings()
db = Database()

templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal"""
    has_api_key = db.has_api_key()
    projects = list_projects(settings.projects_dir)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "has_api_key": has_api_key,
        "projects": projects,
        "current_workspace": None,
        "conversation_id": None,
    })


@router.get("/chat/{conv_id}", response_class=HTMLResponse)
async def chat_page(request: Request, conv_id: int):
    """Página de chat con conversación específica"""
    has_api_key = db.has_api_key()
    projects = list_projects(settings.projects_dir)
    
    # Detectar si es el proyecto principal (test03)
    is_main_project = False
    conv = db.get_conversation(conv_id, by_conv_id=True)
    if conv:
        # Verificar por repo_name o project_name
        repo_name = conv.get('repo_name', '')
        project_name = conv.get('project_name', '')
        if repo_name == 'test03' or 'test03' in project_name.lower():
            is_main_project = True
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "has_api_key": has_api_key,
        "projects": projects,
        "current_workspace": None,
        "conversation_id": conv_id,
        "is_main_project": is_main_project,
    })


@router.get("/settings", response_class=HTMLResponse)
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


@router.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request):
    """Página de historial de conversaciones"""
    return templates.TemplateResponse("conversations.html", {"request": request})
