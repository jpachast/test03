"""
Manejo de workspace (proyectos)
"""

import os
import subprocess
from pathlib import Path


def setup_workspace(identificador: str, tipo: str, projects_dir: Path) -> str:
    """
    Configura el workspace según el tipo
    
    Args:
        identificador: Nombre del proyecto o URL de git
        tipo: "nuevo", "git", o "existente"
        projects_dir: Directorio base de proyectos
    
    Returns:
        Path del workspace
    """
    
    projects_dir.mkdir(parents=True, exist_ok=True)
    
    if tipo == "nuevo":
        # Crear directorio nuevo
        workspace = projects_dir / identificador
        workspace.mkdir(exist_ok=True)
        return str(workspace)
    
    elif tipo == "git":
        # Clonar repositorio
        repo_name = identificador.split("/")[-1].replace(".git", "")
        workspace = projects_dir / repo_name
        
        if workspace.exists():
            # Ya existe, hacer pull
            subprocess.run(
                ["git", "pull"],
                cwd=workspace,
                capture_output=True
            )
        else:
            # Clonar
            subprocess.run(
                ["git", "clone", identificador, str(workspace)],
                capture_output=True
            )
        
        return str(workspace)
    
    elif tipo == "existente":
        # Usar proyecto existente
        workspace = projects_dir / identificador
        if workspace.exists():
            return str(workspace)
        else:
            raise ValueError(f"Proyecto no encontrado: {identificador}")
    
    else:
        raise ValueError(f"Tipo de workspace no válido: {tipo}")


def list_projects(projects_dir: Path) -> list:
    """Lista todos los proyectos"""
    if not projects_dir.exists():
        return []
    
    projects = []
    for item in projects_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            projects.append({
                'name': item.name,
                'path': str(item),
                'is_git': (item / '.git').exists()
            })
    
    return sorted(projects, key=lambda x: x['name'])


def get_project_info(project_path: str) -> dict:
    """Obtiene información de un proyecto"""
    path = Path(project_path)
    
    if not path.exists():
        return None
    
    info = {
        'name': path.name,
        'path': str(path),
        'is_git': (path / '.git').exists(),
        'files': [],
        'git_remote': None,
        'git_branch': None,
    }
    
    # Listar archivos (solo primer nivel)
    for item in path.iterdir():
        if not item.name.startswith('.'):
            info['files'].append({
                'name': item.name,
                'is_dir': item.is_dir()
            })
    
    # Info de git si aplica
    if info['is_git']:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['git_remote'] = result.stdout.strip()
            
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['git_branch'] = result.stdout.strip()
        except:
            pass
    
    return info
