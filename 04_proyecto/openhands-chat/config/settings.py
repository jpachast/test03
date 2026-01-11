"""
Configuración del proyecto
"""

import os
from pathlib import Path


class Settings:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.projects_dir = self.base_dir / "projects"
        
        # Crear directorios si no existen
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración del servidor
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", 8000))
        
        # Modelo por defecto
        self.default_model = os.getenv("LLM_MODEL", "gemini/gemini-2.5-pro")
        
        # Base URL (opcional)
        self.llm_base_url = os.getenv("LLM_BASE_URL", None)
