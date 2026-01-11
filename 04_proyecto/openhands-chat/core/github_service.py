"""
Servicio de GitHub para interactuar con la API
"""

import os
import subprocess
import requests
from pathlib import Path
from typing import Optional, List, Dict


class GitHubService:
    """Servicio para interactuar con GitHub"""
    
    API_BASE = "https://api.github.com"
    
    def __init__(self, token: str = None):
        self.token = token
        self._user_cache = None
    
    def set_token(self, token: str):
        """Establecer token"""
        self.token = token
        self._user_cache = None
    
    def _headers(self) -> dict:
        """Headers para requests"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OpenHands-Chat"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers
    
    def validate_token(self) -> Dict:
        """Validar token y obtener info del usuario"""
        if not self.token:
            return {"valid": False, "error": "No token provided"}
        
        try:
            response = requests.get(
                f"{self.API_BASE}/user",
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                user = response.json()
                self._user_cache = user
                return {
                    "valid": True,
                    "username": user.get("login"),
                    "name": user.get("name"),
                    "avatar_url": user.get("avatar_url"),
                    "public_repos": user.get("public_repos"),
                    "private_repos": user.get("total_private_repos", 0)
                }
            elif response.status_code == 401:
                return {"valid": False, "error": "Token inválido o expirado"}
            else:
                return {"valid": False, "error": f"Error: {response.status_code}"}
        except requests.RequestException as e:
            return {"valid": False, "error": str(e)}
    
    def get_user_repos(self, page: int = 1, per_page: int = 30, 
                        sort: str = "updated") -> Dict:
        """Obtener repositorios del usuario"""
        if not self.token:
            return {"success": False, "error": "No token configured"}
        
        try:
            response = requests.get(
                f"{self.API_BASE}/user/repos",
                headers=self._headers(),
                params={
                    "page": page,
                    "per_page": per_page,
                    "sort": sort,
                    "affiliation": "owner,collaborator,organization_member"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                repos = response.json()
                return {
                    "success": True,
                    "repos": [
                        {
                            "id": repo["id"],
                            "full_name": repo["full_name"],
                            "owner": repo["owner"]["login"],
                            "name": repo["name"],
                            "description": repo.get("description", ""),
                            "private": repo["private"],
                            "default_branch": repo.get("default_branch", "main"),
                            "updated_at": repo["updated_at"],
                            "language": repo.get("language"),
                            "stargazers_count": repo.get("stargazers_count", 0)
                        }
                        for repo in repos
                    ]
                }
            else:
                return {"success": False, "error": f"Error: {response.status_code}"}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_repo_branches(self, owner: str, repo: str) -> Dict:
        """Obtener branches de un repositorio"""
        if not self.token:
            return {"success": False, "error": "No token configured"}
        
        try:
            response = requests.get(
                f"{self.API_BASE}/repos/{owner}/{repo}/branches",
                headers=self._headers(),
                params={"per_page": 100},
                timeout=10
            )
            
            if response.status_code == 200:
                branches = response.json()
                return {
                    "success": True,
                    "branches": [
                        {
                            "name": branch["name"],
                            "protected": branch.get("protected", False)
                        }
                        for branch in branches
                    ]
                }
            elif response.status_code == 404:
                return {"success": False, "error": "Repositorio no encontrado"}
            else:
                return {"success": False, "error": f"Error: {response.status_code}"}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_repo_info(self, owner: str, repo: str) -> Dict:
        """Obtener información de un repositorio"""
        if not self.token:
            return {"success": False, "error": "No token configured"}
        
        try:
            response = requests.get(
                f"{self.API_BASE}/repos/{owner}/{repo}",
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "repo": {
                        "id": data["id"],
                        "full_name": data["full_name"],
                        "owner": data["owner"]["login"],
                        "name": data["name"],
                        "description": data.get("description", ""),
                        "private": data["private"],
                        "default_branch": data.get("default_branch", "main"),
                        "clone_url": data["clone_url"],
                        "ssh_url": data["ssh_url"],
                        "language": data.get("language"),
                        "size": data.get("size", 0)
                    }
                }
            elif response.status_code == 404:
                return {"success": False, "error": "Repositorio no encontrado"}
            else:
                return {"success": False, "error": f"Error: {response.status_code}"}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def clone_repo(self, owner: str, repo: str, branch: str, 
                   target_dir: str) -> Dict:
        """Clonar repositorio"""
        if not self.token:
            return {"success": False, "error": "No token configured"}
        
        # URL con token para repos privados
        clone_url = f"https://{self.token}@github.com/{owner}/{repo}.git"
        target_path = Path(target_dir)
        
        # Crear directorio padre si no existe
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Si ya existe, hacer pull
        if target_path.exists() and (target_path / ".git").exists():
            try:
                # Actualizar remoto con token
                subprocess.run(
                    ["git", "remote", "set-url", "origin", clone_url],
                    cwd=target_path,
                    capture_output=True,
                    check=True
                )
                # Fetch
                subprocess.run(
                    ["git", "fetch", "origin"],
                    cwd=target_path,
                    capture_output=True,
                    check=True
                )
                # Checkout branch
                subprocess.run(
                    ["git", "checkout", branch],
                    cwd=target_path,
                    capture_output=True
                )
                # Pull
                result = subprocess.run(
                    ["git", "pull", "origin", branch],
                    cwd=target_path,
                    capture_output=True,
                    text=True
                )
                return {
                    "success": True,
                    "action": "updated",
                    "path": str(target_path),
                    "message": "Repositorio actualizado"
                }
            except subprocess.CalledProcessError as e:
                return {"success": False, "error": f"Error al actualizar: {e.stderr}"}
        
        # Clonar nuevo
        try:
            result = subprocess.run(
                ["git", "clone", "-b", branch, "--single-branch", clone_url, str(target_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "action": "cloned",
                    "path": str(target_path),
                    "message": "Repositorio clonado exitosamente"
                }
            else:
                return {"success": False, "error": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout al clonar repositorio"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_repos(self, query: str, page: int = 1) -> Dict:
        """Buscar repositorios"""
        if not self.token:
            return {"success": False, "error": "No token configured"}
        
        try:
            # Buscar en repos del usuario primero
            response = requests.get(
                f"{self.API_BASE}/search/repositories",
                headers=self._headers(),
                params={
                    "q": f"{query} user:{self._get_username()}",
                    "page": page,
                    "per_page": 20,
                    "sort": "updated"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "total_count": data.get("total_count", 0),
                    "repos": [
                        {
                            "full_name": repo["full_name"],
                            "owner": repo["owner"]["login"],
                            "name": repo["name"],
                            "description": repo.get("description", ""),
                            "private": repo["private"],
                            "default_branch": repo.get("default_branch", "main")
                        }
                        for repo in data.get("items", [])
                    ]
                }
            else:
                return {"success": False, "error": f"Error: {response.status_code}"}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def _get_username(self) -> str:
        """Obtener username del cache o API"""
        if self._user_cache:
            return self._user_cache.get("login", "")
        result = self.validate_token()
        return result.get("username", "")
