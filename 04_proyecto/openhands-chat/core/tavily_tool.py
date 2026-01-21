"""
Tavily Tool - Herramienta de búsqueda web para el agente OpenHands

Esta herramienta permite al agente realizar búsquedas web en tiempo real
usando la API de Tavily, con tracking de créditos integrado.

Uso:
    El agente puede llamar a esta herramienta cuando necesite:
    - Buscar información actualizada en internet
    - Investigar sobre tecnologías, noticias, documentación
    - Obtener datos en tiempo real
"""

import os
import json
from typing import Optional
from pydantic import BaseModel, Field

# Importar el servicio de Tavily con tracking
from .tavily_service import get_tavily_service, reinit_tavily_service, TavilyService

# Para registrar como Tool del SDK
try:
    from openhands.sdk.tool import BaseTool, ToolResult
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    # Fallback para cuando no está el SDK
    class BaseTool:
        name = ""
        description = ""
    class ToolResult:
        def __init__(self, output="", error=""):
            self.output = output
            self.error = error


class TavilySearchParams(BaseModel):
    """Parámetros para la búsqueda con Tavily"""
    query: str = Field(..., description="La consulta de búsqueda en lenguaje natural")
    search_depth: str = Field(
        default="basic",
        description="Profundidad de búsqueda: 'basic' (1 crédito) o 'advanced' (2 créditos)"
    )
    max_results: int = Field(
        default=5,
        description="Número máximo de resultados (1-10)"
    )
    include_answer: bool = Field(
        default=True,
        description="Incluir respuesta resumida generada por IA"
    )


class TavilyExtractParams(BaseModel):
    """Parámetros para extraer contenido de URLs"""
    urls: list = Field(..., description="Lista de URLs para extraer contenido")


class TavilyTool(BaseTool if SDK_AVAILABLE else object):
    """
    Herramienta de búsqueda web con Tavily.
    
    Permite al agente buscar información actualizada en internet
    y extraer contenido de páginas web específicas.
    
    Características:
    - Búsqueda en tiempo real
    - Respuestas resumidas por IA
    - Tracking de créditos (Plan Free: 1000/mes)
    - Extracción de contenido de URLs
    """
    
    name = "tavily_web_search"
    description = """Busca información en internet en tiempo real usando Tavily.

USO: Cuando el usuario pida buscar algo en internet, noticias actuales, 
información reciente o cualquier dato que requiera una búsqueda web.

PARÁMETROS:
- query: La consulta de búsqueda (requerido)
- search_depth: "basic" (rápido, 1 crédito) o "advanced" (profundo, 2 créditos)
- max_results: Número de resultados (1-10, default: 5)

EJEMPLO:
Para buscar noticias de IA:
{
    "query": "últimas noticias inteligencia artificial 2025",
    "search_depth": "basic",
    "max_results": 5
}

LÍMITES: Plan Free tiene 1000 créditos/mes. El agente debe informar al usuario
si se acercan al límite."""

    # Instancia del servicio (singleton)
    _service: Optional[TavilyService] = None
    
    @classmethod
    def get_service(cls, db=None) -> TavilyService:
        """Obtener instancia del servicio Tavily"""
        if cls._service is None:
            cls._service = get_tavily_service(db)
        return cls._service
    
    @classmethod
    def reinit_service(cls, db=None):
        """Reinicializar el servicio (después de cambiar API key)"""
        cls._service = reinit_tavily_service(db)
        return cls._service

    def execute(self, query: str, search_depth: str = "basic", 
                max_results: int = 5, include_answer: bool = True) -> ToolResult:
        """
        Ejecutar búsqueda web con Tavily.
        
        Args:
            query: Consulta de búsqueda
            search_depth: "basic" o "advanced"
            max_results: Número de resultados (1-10)
            include_answer: Incluir respuesta resumida
            
        Returns:
            ToolResult con los resultados de la búsqueda
        """
        service = self.get_service()
        
        if not service.is_available():
            return ToolResult(
                error="Tavily no está configurado. El usuario debe agregar su API key en Configuración → Integraciones → Tavily."
            )
        
        # Validar parámetros
        max_results = min(max(1, max_results), 10)
        if search_depth not in ["basic", "advanced"]:
            search_depth = "basic"
        
        # Realizar búsqueda
        result = service.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_answer=include_answer
        )
        
        if not result.get("success"):
            return ToolResult(
                error=result.get("error", "Error desconocido en la búsqueda")
            )
        
        # Formatear salida
        output_parts = []
        
        # Agregar respuesta resumida si existe
        if result.get("answer"):
            output_parts.append(f"📝 **Resumen:** {result['answer']}\n")
        
        # Agregar resultados
        output_parts.append(f"🔍 **Resultados para:** \"{query}\"\n")
        
        for i, item in enumerate(result.get("results", []), 1):
            output_parts.append(f"\n**{i}. {item.get('title', 'Sin título')}**")
            output_parts.append(f"   🔗 {item.get('url', '')}")
            content = item.get("content", "")
            if content:
                # Truncar contenido largo
                if len(content) > 300:
                    content = content[:300] + "..."
                output_parts.append(f"   {content}")
        
        # Agregar info de uso
        usage = result.get("usage", {})
        output_parts.append(f"\n---\n💳 Créditos usados: {usage.get('credits_used', 0)}/{usage.get('limit', 1000)} (Plan {usage.get('plan', 'Free')})")
        
        return ToolResult(output="\n".join(output_parts))
    
    def extract(self, urls: list) -> ToolResult:
        """
        Extraer contenido de URLs específicas.
        
        Args:
            urls: Lista de URLs para extraer
            
        Returns:
            ToolResult con el contenido extraído
        """
        service = self.get_service()
        
        if not service.is_available():
            return ToolResult(
                error="Tavily no está configurado."
            )
        
        result = service.extract(urls)
        
        if not result.get("success"):
            return ToolResult(
                error=result.get("error", "Error extrayendo contenido")
            )
        
        output_parts = ["📄 **Contenido extraído:**\n"]
        
        for item in result.get("results", []):
            output_parts.append(f"\n**URL:** {item.get('url', '')}")
            output_parts.append(f"**Contenido:**\n{item.get('raw_content', item.get('content', 'Sin contenido'))[:2000]}")
        
        return ToolResult(output="\n".join(output_parts))


# Función helper para usar sin instanciar
def tavily_search(query: str, search_depth: str = "basic", 
                  max_results: int = 5, db=None) -> dict:
    """
    Función helper para búsqueda rápida con Tavily.
    
    Args:
        query: Consulta de búsqueda
        search_depth: "basic" o "advanced"
        max_results: Número de resultados
        db: Instancia de Database (opcional)
        
    Returns:
        dict con resultados
    """
    service = get_tavily_service(db)
    return service.search(query, search_depth, max_results)


def tavily_extract(urls: list, db=None) -> dict:
    """
    Función helper para extracción de contenido.
    
    Args:
        urls: Lista de URLs
        db: Instancia de Database (opcional)
        
    Returns:
        dict con contenido extraído
    """
    service = get_tavily_service(db)
    return service.extract(urls)


def get_tavily_usage(db=None) -> dict:
    """
    Obtener estadísticas de uso de Tavily.
    
    Returns:
        dict con estadísticas de uso
    """
    service = get_tavily_service(db)
    return service.get_usage_stats()


# Registro de la herramienta para el SDK
TAVILY_TOOL_DEFINITION = {
    "name": "tavily_web_search",
    "description": TavilyTool.description,
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "La consulta de búsqueda en lenguaje natural"
            },
            "search_depth": {
                "type": "string",
                "enum": ["basic", "advanced"],
                "description": "Profundidad: 'basic' (1 crédito) o 'advanced' (2 créditos)",
                "default": "basic"
            },
            "max_results": {
                "type": "integer",
                "description": "Número de resultados (1-10)",
                "default": 5,
                "minimum": 1,
                "maximum": 10
            }
        },
        "required": ["query"]
    }
}
