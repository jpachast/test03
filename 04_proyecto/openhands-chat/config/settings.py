"""
Configuración del proyecto
TODOS los valores están HARDCODEADOS - no dependen de variables de entorno
"""

from pathlib import Path


class Settings:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.projects_dir = self.base_dir / "projects"
        
        # Crear directorios si no existen
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración del servidor - HARDCODEADO
        self.host = "0.0.0.0"
        self.port = 12000  # Puerto fijo para work-1
        
        # Puerto del servidor de proyectos
        self.projects_port = 12001  # Puerto fijo para work-2
        
        # Modelos - DeepSeek para código, Gemini para visión
        self.default_model = "deepseek/deepseek-chat"  # DeepSeek V3
        self.vision_model = "gemini/gemini-2.0-flash"  # Para imágenes
        
        # Base URL (opcional)
        self.llm_base_url = None
