"""
Endpoints API para Diff Preview Visual
Muestra cambios de archivos con highlighting estilo GitHub
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import subprocess
import os
from pathlib import Path

router = APIRouter(prefix="/api/diff", tags=["diff"])


class DiffRequest(BaseModel):
    """Request para obtener diff"""
    workspace: str
    file_path: Optional[str] = None  # None = todos los archivos


class CommitDiffRequest(BaseModel):
    """Request para diff entre commits"""
    workspace: str
    commit1: str = "HEAD~1"
    commit2: str = "HEAD"


def parse_diff_output(diff_output: str) -> List[Dict[str, Any]]:
    """
    Parsea output de git diff a estructura de datos para UI
    """
    files = []
    current_file = None
    
    lines = diff_output.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Nueva archivo en diff
        if line.startswith('diff --git'):
            if current_file:
                files.append(current_file)
            
            # Extraer nombre de archivo
            parts = line.split(' b/')
            file_name = parts[-1] if len(parts) > 1 else "unknown"
            
            current_file = {
                "file": file_name,
                "additions": 0,
                "deletions": 0,
                "chunks": [],
                "status": "modified"
            }
        
        # Archivo nuevo
        elif line.startswith('new file mode'):
            if current_file:
                current_file["status"] = "added"
        
        # Archivo eliminado
        elif line.startswith('deleted file mode'):
            if current_file:
                current_file["status"] = "deleted"
        
        # Línea de contexto (@@ -x,y +a,b @@)
        elif line.startswith('@@') and current_file:
            # Extraer info del chunk
            chunk = {
                "header": line,
                "lines": []
            }
            i += 1
            
            # Leer líneas del chunk hasta el próximo @@ o diff
            while i < len(lines):
                chunk_line = lines[i]
                
                if chunk_line.startswith('diff --git') or chunk_line.startswith('@@'):
                    i -= 1  # Retroceder para procesar en siguiente iteración
                    break
                
                if chunk_line.startswith('+') and not chunk_line.startswith('+++'):
                    chunk["lines"].append({
                        "type": "addition",
                        "content": chunk_line[1:],
                        "line": chunk_line
                    })
                    current_file["additions"] += 1
                elif chunk_line.startswith('-') and not chunk_line.startswith('---'):
                    chunk["lines"].append({
                        "type": "deletion",
                        "content": chunk_line[1:],
                        "line": chunk_line
                    })
                    current_file["deletions"] += 1
                elif not chunk_line.startswith('\\'):  # Ignorar "No newline at end"
                    chunk["lines"].append({
                        "type": "context",
                        "content": chunk_line[1:] if chunk_line.startswith(' ') else chunk_line,
                        "line": chunk_line
                    })
                
                i += 1
            
            current_file["chunks"].append(chunk)
        
        i += 1
    
    # Agregar último archivo
    if current_file:
        files.append(current_file)
    
    return files


@router.post("/staged")
async def get_staged_diff(request: DiffRequest):
    """
    Obtiene diff de cambios staged (git diff --cached)
    """
    try:
        workspace = Path(request.workspace)
        if not workspace.exists():
            raise HTTPException(status_code=404, detail="Workspace no encontrado")
        
        cmd = ["git", "diff", "--cached"]
        if request.file_path:
            cmd.append(request.file_path)
        
        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {"success": False, "error": result.stderr, "files": []}
        
        files = parse_diff_output(result.stdout)
        
        total_additions = sum(f["additions"] for f in files)
        total_deletions = sum(f["deletions"] for f in files)
        
        return {
            "success": True,
            "type": "staged",
            "files": files,
            "summary": {
                "total_files": len(files),
                "additions": total_additions,
                "deletions": total_deletions
            }
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Timeout obteniendo diff")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unstaged")
async def get_unstaged_diff(request: DiffRequest):
    """
    Obtiene diff de cambios no staged (git diff)
    """
    try:
        workspace = Path(request.workspace)
        if not workspace.exists():
            raise HTTPException(status_code=404, detail="Workspace no encontrado")
        
        cmd = ["git", "diff"]
        if request.file_path:
            cmd.append(request.file_path)
        
        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        files = parse_diff_output(result.stdout)
        
        total_additions = sum(f["additions"] for f in files)
        total_deletions = sum(f["deletions"] for f in files)
        
        return {
            "success": True,
            "type": "unstaged",
            "files": files,
            "summary": {
                "total_files": len(files),
                "additions": total_additions,
                "deletions": total_deletions
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commits")
async def get_commit_diff(request: CommitDiffRequest):
    """
    Obtiene diff entre dos commits
    """
    try:
        workspace = Path(request.workspace)
        if not workspace.exists():
            raise HTTPException(status_code=404, detail="Workspace no encontrado")
        
        result = subprocess.run(
            ["git", "diff", request.commit1, request.commit2],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        files = parse_diff_output(result.stdout)
        
        total_additions = sum(f["additions"] for f in files)
        total_deletions = sum(f["deletions"] for f in files)
        
        return {
            "success": True,
            "type": "commits",
            "commit1": request.commit1,
            "commit2": request.commit2,
            "files": files,
            "summary": {
                "total_files": len(files),
                "additions": total_additions,
                "deletions": total_deletions
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_git_status(workspace: str):
    """
    Obtiene estado de git (archivos modificados, staged, etc)
    """
    try:
        workspace_path = Path(workspace)
        if not workspace_path.exists():
            raise HTTPException(status_code=404, detail="Workspace no encontrado")
        
        # Git status porcelain
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        files = {
            "staged": [],
            "unstaged": [],
            "untracked": []
        }
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            status = line[:2]
            file_path = line[3:]
            
            # Staged changes (index)
            if status[0] in ['M', 'A', 'D', 'R', 'C']:
                files["staged"].append({
                    "file": file_path,
                    "status": {
                        'M': 'modified',
                        'A': 'added',
                        'D': 'deleted',
                        'R': 'renamed',
                        'C': 'copied'
                    }.get(status[0], 'unknown')
                })
            
            # Unstaged changes (working tree)
            if status[1] in ['M', 'D']:
                files["unstaged"].append({
                    "file": file_path,
                    "status": 'modified' if status[1] == 'M' else 'deleted'
                })
            
            # Untracked
            if status == '??':
                files["untracked"].append({
                    "file": file_path,
                    "status": "untracked"
                })
        
        return {
            "success": True,
            "files": files,
            "summary": {
                "staged": len(files["staged"]),
                "unstaged": len(files["unstaged"]),
                "untracked": len(files["untracked"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_commit_history(workspace: str, limit: int = 10):
    """
    Obtiene historial de commits recientes
    """
    try:
        workspace_path = Path(workspace)
        if not workspace_path.exists():
            raise HTTPException(status_code=404, detail="Workspace no encontrado")
        
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--pretty=format:%H|%h|%s|%an|%ar"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 5:
                commits.append({
                    "hash": parts[0],
                    "short_hash": parts[1],
                    "message": parts[2],
                    "author": parts[3],
                    "date": parts[4]
                })
        
        return {
            "success": True,
            "commits": commits
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
