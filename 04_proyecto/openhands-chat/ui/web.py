"""
Servidor web FastAPI - Punto de entrada principal

OPTIMIZACIONES:
- Lazy imports para startup más rápido
- GzipMiddleware para comprimir respuestas (-70% tamaño)
- Cache headers para archivos estáticos
"""
from pathlib import Path
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config.database import Database
from config.settings import Settings
from core.workspace import setup_workspace, get_project_info

# OPTIMIZACIÓN: Import routers de forma individual (evita cargar todos al inicio)
from ui.routers.pages import router as pages_router
from ui.routers.settings import router as settings_router
from ui.routers.github import router as github_router
from ui.routers.conversations import router as conversations_router
from ui.routers.chat import router as chat_router
from ui.routers.git import router as git_router
from ui.routers.code_server import router as code_server_router
from ui.routers.projects_server import router as projects_server_router
from ui.routers.browser import router as browser_router

# OPTIMIZACIÓN: Middleware para cache de archivos estáticos
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Cache para archivos estáticos (CSS, JS, imágenes)
        if request.url.path.startswith("/static/"):
            # Si tiene query string (cache-buster), cache muy largo (1 año)
            # Si no tiene, cache corto (1 hora)
            if request.url.query:
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                response.headers["Cache-Control"] = "public, max-age=3600"
        return response

# Inicializar
app = FastAPI(title="OpenHands Chat", version="2.0.0")

# OPTIMIZACIÓN: Comprimir respuestas >500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)
# OPTIMIZACIÓN: Cache headers para estáticos
app.add_middleware(CacheControlMiddleware)

settings = Settings()
db = Database()

# Static files
static_dir = Path(__file__).parent.parent / "static"
projects_dir = Path(__file__).parent.parent / "projects"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if projects_dir.exists():
    app.mount("/projects", StaticFiles(directory=str(projects_dir), html=True), name="projects")

# Registrar routers
app.include_router(pages_router)
app.include_router(settings_router)
app.include_router(github_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(git_router)
app.include_router(code_server_router)
app.include_router(projects_server_router)
app.include_router(browser_router)


# === RUTAS DE PROYECTOS (legacy) ===

@app.post("/api/project/new")
async def create_project(name: str = Form(...)):
    """Crear nuevo proyecto"""
    try:
        workspace = setup_workspace(name, "nuevo", settings.projects_dir)
        db.add_project(name, workspace)
        return RedirectResponse(url=f"/?project={name}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/project/clone")
async def clone_project(git_url: str = Form(...)):
    """Clonar proyecto de Git"""
    try:
        workspace = setup_workspace(git_url, "git", settings.projects_dir)
        name = Path(workspace).name
        
        # Extraer repo_owner, repo_name, branch de la URL
        repo_owner = None
        repo_name = None
        branch = "main"
        
        # Parsear URL de GitHub: https://github.com/owner/repo.git
        import re
        match = re.search(r'github\.com[/:]([^/]+)/([^/.]+)', git_url)
        if match:
            repo_owner = match.group(1)
            repo_name = match.group(2)
        
        if repo_owner and repo_name:
            db.add_project_with_repo(name, workspace, repo_owner, repo_name, branch, git_url)
        else:
            db.add_project(name, workspace, git_url)
        
        return RedirectResponse(url=f"/?project={name}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/project/select")
async def select_project(name: str = Form(...)):
    """Seleccionar proyecto existente"""
    try:
        setup_workspace(name, "existente", settings.projects_dir)
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


# === HEALTH CHECK ===

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "has_api_key": db.has_api_key(),
        "has_github": db.has_github_token()
    }
