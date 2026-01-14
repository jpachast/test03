"""Rutas de operaciones Git"""
import subprocess
import requests
from fastapi import APIRouter
from pydantic import BaseModel

from config.database import Database
from config.settings import Settings
from core.github_service import GitHubService

router = APIRouter(prefix="/api/git", tags=["git"])
db = Database()
settings = Settings()
github_service = GitHubService()


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


@router.post("/pull")
async def git_pull(request: GitPullRequest):
    """Hacer git pull en el proyecto (clona si no existe)"""
    project_path = settings.projects_dir / request.project
    
    token = db.get_github_token()
    if not token:
        return {"success": False, "error": "GitHub no configurado"}
    
    # Si el proyecto no existe, clonarlo primero
    if not project_path.exists() or not (project_path / ".git").exists():
        try:
            project_path.mkdir(parents=True, exist_ok=True)
            clone_url = f"https://{token}@github.com/{request.owner}/{request.repo}.git"
            
            result = subprocess.run(
                ["git", "clone", "-b", request.branch, clone_url, str(project_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Configurar git user
                username = db.get_github_username() or "openhands"
                subprocess.run(["git", "config", "user.email", f"{username}@users.noreply.github.com"], 
                             cwd=str(project_path))
                subprocess.run(["git", "config", "user.name", username], cwd=str(project_path))
                return {"success": True, "message": "Repositorio clonado exitosamente", "action": "cloned"}
            else:
                return {"success": False, "error": result.stderr or "Error clonando repositorio"}
        except Exception as e:
            return {"success": False, "error": f"Error clonando: {str(e)}"}
    
    # Si ya existe, hacer pull normal
    try:
        # Actualizar remote URL con token actual
        remote_url = f"https://{token}@github.com/{request.owner}/{request.repo}.git"
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], cwd=str(project_path))
        
        result = subprocess.run(
            ["git", "pull", "origin", request.branch],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {"success": True, "message": result.stdout or "Pull exitoso", "action": "pulled"}
        return {"success": False, "error": result.stderr or "Error en pull"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout en operación"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/push")
async def git_push(request: GitPushRequest):
    """Hacer git add, commit y push"""
    project_path = settings.projects_dir / request.project
    
    if not project_path.exists():
        return {"success": False, "error": "Proyecto no encontrado"}
    
    token = db.get_github_token()
    if not token:
        return {"success": False, "error": "GitHub no configurado"}
    
    username = db.get_github_username() or "openhands"
    
    try:
        subprocess.run(
            ["git", "config", "user.email", f"{username}@users.noreply.github.com"],
            cwd=str(project_path), check=True
        )
        subprocess.run(
            ["git", "config", "user.name", username],
            cwd=str(project_path), check=True
        )
        
        subprocess.run(["git", "add", "-A"], cwd=str(project_path), check=True)
        
        result = subprocess.run(
            ["git", "commit", "-m", request.commit_message],
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and "nothing to commit" in (result.stdout + result.stderr):
            return {"success": False, "error": "No hay cambios para commitear"}
        
        remote_url = f"https://{token}@github.com/{request.owner}/{request.repo}.git"
        subprocess.run(
            ["git", "remote", "set-url", "origin", remote_url],
            cwd=str(project_path), check=True
        )
        
        result = subprocess.run(
            ["git", "push", "origin", request.branch],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "Push exitoso"}
        return {"success": False, "error": result.stderr or "Error en push"}
            
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/create-pr")
async def git_create_pr(request: GitPRRequest):
    """Crear Pull Request en GitHub"""
    token = db.get_github_token()
    if not token:
        return {"success": False, "error": "GitHub no configurado"}
    
    github_service.set_token(token)
    
    try:
        headers = {"Authorization": f"token {token}"}
        repo_info = requests.get(
            f"https://api.github.com/repos/{request.owner}/{request.repo}",
            headers=headers
        ).json()
        
        default_branch = repo_info.get("default_branch", "main")
        
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
        
        error_msg = response.json().get("message", "Error creando PR")
        return {"success": False, "error": error_msg}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
