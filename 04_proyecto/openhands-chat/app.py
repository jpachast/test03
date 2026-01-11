#!/usr/bin/env python3
"""
OpenHands Chat - Punto de entrada principal
"""

import uvicorn
from config.settings import Settings

def main():
    """Iniciar servidor"""
    settings = Settings()
    
    print("=" * 60)
    print("  🤖 OPENHANDS CHAT")
    print("=" * 60)
    print(f"  🌐 Servidor: http://{settings.host}:{settings.port}")
    print(f"  📁 Proyectos: {settings.projects_dir}")
    print("=" * 60)
    print()
    print("  Abre tu navegador en la URL de arriba")
    print("  Presiona Ctrl+C para detener")
    print()
    
    uvicorn.run(
        "ui.web:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
