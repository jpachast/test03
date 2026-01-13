"""Rutas de GitHub"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config.database import Database
from config.settings import Settings
from core.github_service import GitHubService

router = APIRouter(prefix="/api/github", tags=["github"])
db = Database()
settings = Settings()
github_service = GitHubService()


class GitHubTokenRequest(BaseModel):
    token: str


class LaunchRepoRequest(BaseModel):
    owner: str
    repo: str
    branch: str = "main"


@router.get("/status")
async def github_status():
    """Estado de la configuración de GitHub"""
    has_token = db.has_github_token()
    username = db.get_github_username() if has_token else None
    return {"configured": has_token, "username": username}


@router.post("/token")
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
    return JSONResponse({"success": False, "error": result.get("error", "Token inválido")}, status_code=400)


@router.delete("/token")
async def delete_github_token():
    """Eliminar token de GitHub"""
    db.delete_setting("github_token")
    db.delete_setting("github_username")
    github_service.set_token(None)
    return {"success": True}


@router.get("/repos")
async def get_github_repos(page: int = 1, per_page: int = 30):
    """Obtener repositorios del usuario"""
    token = db.get_github_token()
    if not token:
        raise HTTPException(status_code=401, detail="GitHub no configurado")
    
    github_service.set_token(token)
    result = github_service.get_user_repos(page, per_page)
    
    if result.get("success"):
        return result
    raise HTTPException(status_code=500, detail=result.get("error"))


@router.get("/repos/{owner}/{repo}/branches")
async def get_repo_branches(owner: str, repo: str):
    """Obtener branches de un repositorio"""
    token = db.get_github_token()
    if not token:
        raise HTTPException(status_code=401, detail="GitHub no configurado")
    
    github_service.set_token(token)
    result = github_service.get_repo_branches(owner, repo)
    
    if result.get("success"):
        return result
    raise HTTPException(status_code=500, detail=result.get("error"))


@router.post("/launch")
async def launch_repo(request: LaunchRepoRequest):
    """Iniciar/clonar un repositorio y crear conversación"""
    token = db.get_github_token()
    if not token:
        raise HTTPException(status_code=401, detail="GitHub no configurado")
    
    github_service.set_token(token)
    
    is_main = (request.owner == "jpachast" and request.repo == "test03")
    
    repo_folder = f"{request.owner}-{request.repo}"
    repo_base_path = settings.projects_dir / repo_folder
    repo_base_path.mkdir(parents=True, exist_ok=True)
    
    existing_chats = list(repo_base_path.glob("chat*"))
    chat_num = len(existing_chats) + 1
    chat_folder = f"chat{chat_num:02d}"
    chat_path = repo_base_path / chat_folder
    
    if is_main:
        chat_path.mkdir(parents=True, exist_ok=True)
        action = "created"
    else:
        clone_result = github_service.clone_repo(request.owner, request.repo, request.branch, str(chat_path))
        if not clone_result.get("success"):
            raise HTTPException(status_code=500, detail=clone_result.get("error"))
        action = "cloned"
    
    git_url = f"https://github.com/{request.owner}/{request.repo}.git"
    project_id = db.add_project_with_repo(
        name=f"{repo_folder}/{chat_folder}",
        path=str(chat_path),
        repo_owner=request.owner,
        repo_name=request.repo,
        branch=request.branch,
        git_url=git_url
    )
    
    conv_id = db.create_conversation(project_id, f"Trabajo en {request.repo}")
    
    return {
        "success": True,
        "project_id": project_id,
        "conversation_id": conv_id,
        "project_name": f"{repo_folder}/{chat_folder}",
        "path": str(chat_path),
        "action": action
    }
