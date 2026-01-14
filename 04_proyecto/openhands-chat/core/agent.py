"""
Configuración del agente OpenHands
BASADO 100% EN LA DOCUMENTACIÓN OFICIAL Y PROMPTS DE REFERENCIA

Incluye:
- Prompts completos de OpenHands (SYSTEM_PROMPT_COMPLETO, IN_CONTEXT_EXAMPLE, REGLAS_AGENTE)
- Condenser LLM para manejar contextos largos (como OpenHands)
- Herramientas de browser para navegación web con screenshots

El agente usa el CLI de browser para navegar (python -m core.browser).

⚠️ IMPORTANTE - NO AGREGAR tools= AL AGENTE ⚠️
================================================================================
El SDK de OpenHands provee las herramientas AUTOMÁTICAMENTE.
NO existen: TerminalTool, FileEditorTool, BashTool como tools registrados.

CORRECTO:
    agent = Agent(llm=llm, agent_context=agent_context, condenser=condenser)

INCORRECTO (causa KeyError):
    agent = Agent(..., tools=[Tool(name="TerminalTool")])  # NO EXISTE!
    agent = Agent(..., tools=[Tool(name="FileEditorTool")])  # NO EXISTE!

Las únicas tools built-in son: FinishTool, ThinkTool
El agente puede ejecutar bash, editar archivos, etc. SIN especificar tools.
================================================================================
"""
import os

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext
from openhands.sdk.context import Skill
from openhands.sdk.context.condenser import LLMSummarizingCondenser

from config.rules import REGLAS_AGENTE, SYSTEM_PROMPT_COMPLETO, IN_CONTEXT_EXAMPLE


# Directorio de la aplicación (para browser CLI)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BROWSER_INSTRUCTIONS = f"""
## HERRAMIENTAS DE NAVEGACIÓN WEB

Tienes acceso a un browser headless mediante comandos de terminal.
Para navegar en la web, usa estos comandos:

### Navegar a una URL:
```bash
cd {APP_DIR} && python -m core.browser navigate "https://www.google.com"
```

### Obtener estado actual (URL, título, elementos):
```bash
cd {APP_DIR} && python -m core.browser state
```

### Hacer clic en un elemento:
```bash
cd {APP_DIR} && python -m core.browser click "button.submit"
```

### Escribir en un campo:
```bash
cd {APP_DIR} && python -m core.browser type "input#search" "texto a buscar"
```

### Hacer scroll:
```bash
cd {APP_DIR} && python -m core.browser scroll down
```

### Obtener contenido de texto:
```bash
cd {APP_DIR} && python -m core.browser content
```

Los comandos retornan JSON con:
- success: true/false
- url: URL actual
- title: título de la página
- screenshot: imagen en base64 (se muestra automáticamente en la UI)
- elements: elementos interactivos (para state)
- content: texto de la página (para content)

IMPORTANTE: Los screenshots se muestran automáticamente en la pestaña "Navegador" de la UI.
"""


def create_agent(api_key: str, model: str = "gemini/gemini-2.5-pro", base_url: str = None) -> Agent:
    """
    Crea y configura el agente OpenHands
    
    IMPORTANTE: Usa LLMSummarizingCondenser para manejar contextos largos,
    exactamente como lo hace OpenHands. Esto permite usar prompts completos
    sin reducirlos, resumiendo automáticamente el historial cuando es necesario.
    
    Args:
        api_key: API key del LLM
        model: Modelo a usar (default: gemini/gemini-2.5-pro)
        base_url: URL base del LLM (opcional)
    
    Returns:
        Agent configurado con TODAS las tools, reglas y condenser
    """
    
    # Configurar LLM principal para el agente
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
    )
    
    # === CONDENSER: Manejo de contextos largos (como OpenHands) ===
    # El condenser resume automáticamente el historial cuando excede max_size
    # o max_tokens. Usa el mismo LLM para generar resúmenes.
    # Referencia: https://docs.openhands.dev/sdk/guides/context-condenser
    condenser = LLMSummarizingCondenser(
        llm=llm,  # Usa el mismo LLM para resumir
        max_size=240,  # Máximo de eventos antes de condensar
        max_tokens=None,  # Opcional: límite de tokens (None = sin límite)
        keep_first=2,  # Mantener primeros N eventos (system prompt, etc.)
    )
    
    # Combinar reglas con instrucciones de browser
    full_rules = REGLAS_AGENTE + "\n\n" + BROWSER_INSTRUCTIONS
    
    # === CONTEXT CON TODOS LOS PROMPTS INTEGRADOS ===
    # OpenHands usa prompts largos y completos, el condenser maneja
    # la reducción de contexto cuando es necesario.
    agent_context = AgentContext(
        skills=[
            # System prompt completo (basado en system_prompt.j2)
            Skill(
                name="system_prompt_completo",
                content=SYSTEM_PROMPT_COMPLETO,
                source=None,
                trigger=None,  # Siempre activo
            ),
            # Ejemplo de aprendizaje en contexto (basado en in_context_learning_example.j2)
            Skill(
                name="in_context_example",
                content=IN_CONTEXT_EXAMPLE,
                source=None,
                trigger=None,  # Siempre activo
            ),
            # Reglas de comportamiento personalizadas + idioma español + browser
            Skill(
                name="reglas_comportamiento",
                content=full_rules,
                source=None,
                trigger=None,  # Siempre activo
            ),
        ],
        system_message_suffix=full_rules,
        load_public_skills=True,
    )
    
    # Crear agente con:
    # - LLM configurado
    # - Condenser para manejar contextos largos
    # - El SDK provee herramientas automáticamente (bash, file edit, etc.)
    #
    # ⚠️ NO AGREGAR tools=[] - Ver docstring al inicio del archivo
    agent = Agent(
        llm=llm,
        agent_context=agent_context,
        condenser=condenser,  # <-- Esto es lo que usa OpenHands para prompts largos
        # NO AGREGAR: tools=[Tool(name="...")] - causa KeyError!
    )
    
    return agent
