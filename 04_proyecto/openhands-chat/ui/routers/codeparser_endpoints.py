"""
Endpoints API para Code Parser - Chat Sandbox Integration
Parser AST, syntax highlighting themes, autocompletado
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.code_parser import CodeDetector, AutoCompleter, get_code_detector, get_auto_completer

router = APIRouter(prefix="/api/codeparser", tags=["codeparser"])


class ParseCodeRequest(BaseModel):
    """Request para parsear código"""
    code: str
    language: Optional[str] = None


class ExtractBlocksRequest(BaseModel):
    """Request para extraer bloques de código"""
    text: str


class AutocompleteRequest(BaseModel):
    """Request para autocompletado"""
    code: str
    cursor_position: int
    language: str = "python"


# Temas de syntax highlighting disponibles
SYNTAX_THEMES = {
    "dark": {
        "name": "Dark (Default)",
        "background": "#1e1e1e",
        "text": "#d4d4d4",
        "keyword": "#569cd6",
        "string": "#ce9178",
        "number": "#b5cea8",
        "comment": "#6a9955",
        "function": "#dcdcaa",
        "class": "#4ec9b0",
        "variable": "#9cdcfe",
        "operator": "#d4d4d4"
    },
    "monokai": {
        "name": "Monokai",
        "background": "#272822",
        "text": "#f8f8f2",
        "keyword": "#f92672",
        "string": "#e6db74",
        "number": "#ae81ff",
        "comment": "#75715e",
        "function": "#a6e22e",
        "class": "#66d9ef",
        "variable": "#f8f8f2",
        "operator": "#f92672"
    },
    "dracula": {
        "name": "Dracula",
        "background": "#282a36",
        "text": "#f8f8f2",
        "keyword": "#ff79c6",
        "string": "#f1fa8c",
        "number": "#bd93f9",
        "comment": "#6272a4",
        "function": "#50fa7b",
        "class": "#8be9fd",
        "variable": "#f8f8f2",
        "operator": "#ff79c6"
    },
    "github-dark": {
        "name": "GitHub Dark",
        "background": "#0d1117",
        "text": "#c9d1d9",
        "keyword": "#ff7b72",
        "string": "#a5d6ff",
        "number": "#79c0ff",
        "comment": "#8b949e",
        "function": "#d2a8ff",
        "class": "#7ee787",
        "variable": "#c9d1d9",
        "operator": "#ff7b72"
    },
    "solarized-dark": {
        "name": "Solarized Dark",
        "background": "#002b36",
        "text": "#839496",
        "keyword": "#859900",
        "string": "#2aa198",
        "number": "#d33682",
        "comment": "#586e75",
        "function": "#268bd2",
        "class": "#b58900",
        "variable": "#839496",
        "operator": "#93a1a1"
    },
    "nord": {
        "name": "Nord",
        "background": "#2e3440",
        "text": "#d8dee9",
        "keyword": "#81a1c1",
        "string": "#a3be8c",
        "number": "#b48ead",
        "comment": "#616e88",
        "function": "#88c0d0",
        "class": "#8fbcbb",
        "variable": "#d8dee9",
        "operator": "#81a1c1"
    }
}


@router.post("/parse")
async def parse_code(request: ParseCodeRequest):
    """
    Parsea código usando AST real.
    
    - Para Python: usa módulo ast
    - Para JavaScript: usa regex avanzado
    - Detecta funciones, clases, imports, variables
    """
    try:
        detector = get_code_detector()
        result = detector.validate_code(request.code, request.language)
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-blocks")
async def extract_code_blocks(request: ExtractBlocksRequest):
    """
    Extrae bloques de código de un texto/mensaje.
    
    Detecta:
    - Bloques markdown ```lang ... ```
    - Detecta lenguaje automáticamente
    - Parsea AST de cada bloque
    """
    try:
        detector = get_code_detector()
        blocks = detector.extract_code_blocks(request.text)
        
        return {
            "success": True,
            "blocks": [b.to_dict() for b in blocks],
            "count": len(blocks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-language")
async def detect_language(request: ParseCodeRequest):
    """Detecta el lenguaje de un bloque de código"""
    try:
        detector = get_code_detector()
        language = detector.detect_language(request.code)
        
        return {
            "success": True,
            "language": language.value,
            "confidence": "high" if language.value != "unknown" else "low"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/autocomplete")
async def get_autocomplete(request: AutocompleteRequest):
    """
    Obtiene sugerencias de autocompletado.
    
    Soporta:
    - Python keywords y builtins
    - JavaScript keywords y globals
    """
    try:
        completer = get_auto_completer()
        suggestions = completer.get_suggestions(
            code=request.code,
            cursor_pos=request.cursor_position,
            language=request.language
        )
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/themes")
async def get_themes():
    """Obtiene todos los temas de syntax highlighting disponibles"""
    return {
        "success": True,
        "themes": SYNTAX_THEMES,
        "default": "dark"
    }


@router.get("/themes/{theme_id}")
async def get_theme(theme_id: str):
    """Obtiene un tema específico"""
    if theme_id not in SYNTAX_THEMES:
        raise HTTPException(status_code=404, detail=f"Tema no encontrado: {theme_id}")
    
    return {
        "success": True,
        "theme": SYNTAX_THEMES[theme_id],
        "theme_id": theme_id
    }


@router.get("/status")
async def get_status():
    """Estado del sistema de Code Parser"""
    return {
        "status": "active",
        "features": [
            "Parser AST real para Python",
            "Parser regex para JavaScript/TypeScript",
            "Detección automática de lenguaje",
            "Extracción de bloques de código",
            "Autocompletado para Python y JavaScript",
            "6 temas de syntax highlighting"
        ],
        "supported_languages": [
            "python", "javascript", "typescript", 
            "html", "css", "json", "bash", "sql"
        ],
        "themes_available": list(SYNTAX_THEMES.keys())
    }
