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
from ui.routers.multiagent_endpoints import router as multiagent_router
from ui.routers.sandbox_endpoints import router as sandbox_router
from ui.routers.autohealer_endpoints import router as autohealer_router
from ui.routers.testgen_endpoints import router as testgen_router
from ui.routers.scraper_endpoints import router as scraper_router
from ui.routers.tavily_endpoints import router as tavily_router
from ui.routers.mcts_endpoints import router as mcts_router
from ui.routers.semantic_endpoints import router as semantic_router
from ui.routers.diff_endpoints import router as diff_router

# OPTIMIZACIÓN: Middleware para cache de archivos estáticos
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Cache solo para imágenes/fonts - NO para CSS/JS (permiten hot-reload del agente)
        if request.url.path.startswith("/static/"):
            path = request.url.path.lower()
            if any(ext in path for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf']):
                response.headers["Cache-Control"] = "public, max-age=86400"  # 1 día para imágenes
            else:
                response.headers["Cache-Control"] = "no-cache, must-revalidate"  # Sin cache para CSS/JS
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
# Advanced features routers
app.include_router(multiagent_router)
app.include_router(sandbox_router)
app.include_router(autohealer_router)
app.include_router(testgen_router)
app.include_router(scraper_router)
app.include_router(tavily_router)
app.include_router(mcts_router)
app.include_router(semantic_router)
app.include_router(diff_router)


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
