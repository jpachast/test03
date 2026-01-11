# 🏗️ ARQUITECTURA DEL PROYECTO: Chat OpenHands

## 🎯 Casos de Uso

1. **Crear proyectos nuevos desde cero**
2. **Conectar repo Git existente para hacer mejoras**

---

## 📁 Estructura del Proyecto

```
openhands-chat/
├── app.py                    # Punto de entrada principal
├── config/
│   ├── __init__.py
│   ├── settings.py           # Configuración (API keys, modelo, etc.)
│   └── rules.py              # Reglas de comportamiento del agente
├── core/
│   ├── __init__.py
│   ├── agent.py              # Configuración del agente
│   ├── conversation.py       # Manejo de conversaciones
│   └── workspace.py          # Manejo de workspace (nuevo o git clone)
├── ui/
│   ├── __init__.py
│   ├── cli.py                # Interfaz de línea de comandos
│   └── web.py                # (Opcional) Interfaz web con FastAPI
├── requirements.txt          # Dependencias
├── .env.example              # Ejemplo de variables de entorno
└── README.md                 # Documentación
```

---

## 🔄 Flujo de Uso

### Opción 1: Proyecto Nuevo

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Usuario: python app.py                                         │
│                                                                 │
│  Chat: ¿Qué quieres hacer?                                      │
│        1. Crear proyecto nuevo                                  │
│        2. Trabajar en repo existente                            │
│                                                                 │
│  Usuario: 1                                                     │
│                                                                 │
│  Chat: ¿Nombre del proyecto?                                    │
│  Usuario: mi-crm                                                │
│                                                                 │
│  Chat: ✅ Workspace creado en ./projects/mi-crm                 │
│        ¿Qué quieres crear?                                      │
│                                                                 │
│  Usuario: Un CRM con login, dashboard y API REST                │
│                                                                 │
│  Chat: [Ejecuta todo el proyecto...]                            │
│        🌐 Tu app está en: http://localhost:3000                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Opción 2: Repo Git Existente

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Usuario: python app.py                                         │
│                                                                 │
│  Chat: ¿Qué quieres hacer?                                      │
│        1. Crear proyecto nuevo                                  │
│        2. Trabajar en repo existente                            │
│                                                                 │
│  Usuario: 2                                                     │
│                                                                 │
│  Chat: URL del repositorio Git:                                 │
│  Usuario: https://github.com/usuario/mi-proyecto.git            │
│                                                                 │
│  Chat: ✅ Repo clonado en ./projects/mi-proyecto                │
│        Analizando proyecto...                                   │
│        - Framework: React + Node                                │
│        - BD: MongoDB                                            │
│        ¿Qué mejoras quieres hacer?                              │
│                                                                 │
│  Usuario: Agrega autenticación con JWT                          │
│                                                                 │
│  Chat: [Analiza código existente, agrega JWT...]                │
│        ✅ Autenticación agregada                                │
│        ¿Quieres crear un PR con los cambios?                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Código Principal

### `app.py`

```python
#!/usr/bin/env python3
"""
OpenHands Chat - Punto de entrada principal
"""

import os
from core.agent import create_agent
from core.workspace import setup_workspace
from core.conversation import ChatLoop
from config.settings import Settings

def main():
    # Cargar configuración
    settings = Settings()
    
    # Mostrar menú inicial
    print("=" * 60)
    print("  🤖 OPENHANDS CHAT")
    print("=" * 60)
    print("\n¿Qué quieres hacer?\n")
    print("  1. Crear proyecto nuevo")
    print("  2. Trabajar en repo Git existente")
    print("  3. Continuar proyecto anterior")
    print()
    
    opcion = input("Selecciona (1/2/3): ").strip()
    
    # Configurar workspace
    if opcion == "1":
        nombre = input("\n¿Nombre del proyecto? ").strip()
        workspace = setup_workspace(nombre, tipo="nuevo")
    elif opcion == "2":
        url = input("\nURL del repositorio Git: ").strip()
        workspace = setup_workspace(url, tipo="git")
    else:
        workspace = setup_workspace(None, tipo="anterior")
    
    # Crear agente
    agent = create_agent(settings)
    
    # Iniciar chat
    chat = ChatLoop(agent=agent, workspace=workspace)
    chat.run()

if __name__ == "__main__":
    main()
```

### `config/settings.py`

```python
"""Configuración del proyecto"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemini/gemini-2.5-pro")
    llm_base_url: str | None = os.getenv("LLM_BASE_URL", None)
    
    # Workspace
    projects_dir: str = os.getenv("PROJECTS_DIR", "./projects")
    
    # Git
    github_token: str | None = os.getenv("GITHUB_TOKEN", None)
    
    class Config:
        env_file = ".env"
```

### `config/rules.py`

```python
"""Reglas de comportamiento del agente"""

REGLAS_AGENTE = """
REGLAS DE COMPORTAMIENTO:

═══════════════════════════════════════════════════════════════
PARA CONSULTAS Y PREGUNTAS
═══════════════════════════════════════════════════════════════
- Responde de forma clara y directa
- Si el usuario pregunta algo, RESPONDE sin crear código innecesario
- No asumas que quiere un proyecto si solo hace una pregunta

═══════════════════════════════════════════════════════════════
PARA PROYECTOS Y CÓDIGO
═══════════════════════════════════════════════════════════════
- Usa task_tracker para organizar tareas complejas
- Completa cada paso antes de continuar
- Si hay error, corrígelo antes de avanzar
- Instala dependencias automáticamente si faltan
- Al terminar un proyecto con UI, despliega y muestra el link

═══════════════════════════════════════════════════════════════
PARA REPOS EXISTENTES
═══════════════════════════════════════════════════════════════
- Primero analiza la estructura del proyecto
- Identifica el framework, lenguaje y dependencias
- Respeta el estilo de código existente
- NO modifiques código que ya funciona
- Ofrece crear PR con los cambios

═══════════════════════════════════════════════════════════════
PARA CORRECCIÓN DE ERRORES
═══════════════════════════════════════════════════════════════
- Lee el error completo
- Identifica el archivo y línea exacta
- Corrige SOLO lo que tiene el error
- NO TOQUES código que ya funciona
- Si no estás seguro qué archivo tocar, PREGUNTA

═══════════════════════════════════════════════════════════════
PARA DESPLIEGUE
═══════════════════════════════════════════════════════════════
- Si el proyecto tiene UI, inicia el servidor
- Muestra el link: "🌐 Tu app está en: http://localhost:XXXX"
- Si es API, muestra cómo probarla

═══════════════════════════════════════════════════════════════
PARA GIT
═══════════════════════════════════════════════════════════════
- Trabaja en una rama nueva, NUNCA en main/master
- Haz commits descriptivos
- Ofrece crear PR cuando termines las mejoras
- Sincroniza cambios antes de empezar
"""
```

### `core/workspace.py`

```python
"""Manejo de workspace"""

import os
import subprocess
from pathlib import Path

def setup_workspace(identificador: str, tipo: str) -> str:
    """Configura el workspace según el tipo"""
    
    projects_dir = Path(os.getenv("PROJECTS_DIR", "./projects"))
    projects_dir.mkdir(exist_ok=True)
    
    if tipo == "nuevo":
        # Crear directorio nuevo
        workspace = projects_dir / identificador
        workspace.mkdir(exist_ok=True)
        print(f"\n✅ Workspace creado en: {workspace}")
        return str(workspace)
    
    elif tipo == "git":
        # Clonar repositorio
        repo_name = identificador.split("/")[-1].replace(".git", "")
        workspace = projects_dir / repo_name
        
        if workspace.exists():
            print(f"\n📁 Proyecto ya existe, actualizando...")
            subprocess.run(["git", "pull"], cwd=workspace)
        else:
            print(f"\n⏳ Clonando repositorio...")
            subprocess.run(["git", "clone", identificador, str(workspace)])
        
        print(f"✅ Repo listo en: {workspace}")
        return str(workspace)
    
    else:
        # Usar último proyecto
        proyectos = list(projects_dir.iterdir())
        if proyectos:
            ultimo = max(proyectos, key=os.path.getmtime)
            print(f"\n✅ Continuando en: {ultimo}")
            return str(ultimo)
        else:
            print("\n❌ No hay proyectos anteriores")
            return setup_workspace(input("Nombre del nuevo proyecto: "), "nuevo")
```

### `core/agent.py`

```python
"""Configuración del agente"""

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext, Tool
from openhands.sdk.context import Skill
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.browser_use import BrowserUseTool
from openhands.tools.glob import GlobTool
from openhands.tools.grep import GrepTool

from config.settings import Settings
from config.rules import REGLAS_AGENTE

def create_agent(settings: Settings) -> Agent:
    """Crea y configura el agente"""
    
    # LLM
    llm = LLM(
        model=settings.llm_model,
        api_key=SecretStr(settings.llm_api_key),
        base_url=settings.llm_base_url,
    )
    
    # Tools
    tools = [
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
        Tool(name=BrowserUseTool.name),
        Tool(name=GlobTool.name),
        Tool(name=GrepTool.name),
    ]
    
    # Context con reglas
    agent_context = AgentContext(
        skills=[
            Skill(
                name="reglas_comportamiento",
                content=REGLAS_AGENTE,
                trigger=None,
            ),
        ],
        system_message_suffix=REGLAS_AGENTE,
        load_public_skills=True,
    )
    
    # Crear agente
    agent = Agent(
        llm=llm,
        tools=tools,
        agent_context=agent_context,
    )
    
    return agent
```

### `core/conversation.py`

```python
"""Manejo de conversaciones"""

from openhands.sdk import Conversation

class ChatLoop:
    def __init__(self, agent, workspace: str):
        self.conversation = Conversation(agent=agent, workspace=workspace)
        self.workspace = workspace
    
    def run(self):
        """Loop principal del chat"""
        
        print("\n" + "=" * 60)
        print(f"  📁 Workspace: {self.workspace}")
        print("  💬 Escribe tu mensaje (o 'salir' para terminar)")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n👤 Tú: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'salir', 'quit', 'q']:
                    self._mostrar_resumen()
                    break
                
                # Enviar mensaje y ejecutar
                self.conversation.send_message(user_input)
                self.conversation.run()
                
            except KeyboardInterrupt:
                self._mostrar_resumen()
                break
    
    def _mostrar_resumen(self):
        """Muestra resumen al salir"""
        print("\n" + "=" * 60)
        print("  👋 ¡Hasta luego!")
        print(f"  📁 Tu proyecto está en: {self.workspace}")
        
        # Mostrar costo si está disponible
        try:
            cost = self.conversation.agent.llm.metrics.accumulated_cost
            print(f"  💰 Costo de la sesión: ${cost:.4f}")
        except:
            pass
        
        print("=" * 60)
```

### `requirements.txt`

```
openhands-sdk>=1.8.0
openhands-tools>=1.8.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
```

### `.env.example`

```bash
# LLM Configuration
LLM_API_KEY=tu-api-key-de-gemini
LLM_MODEL=gemini/gemini-2.5-pro

# Workspace
PROJECTS_DIR=./projects

# Git (opcional, para crear PRs)
GITHUB_TOKEN=tu-github-token
```

---

## 🚀 Cómo Usarlo

### 1. Instalar

```bash
# Clonar el proyecto
git clone https://github.com/tu-usuario/openhands-chat.git
cd openhands-chat

# Instalar dependencias
pip install -r requirements.txt

# Configurar
cp .env.example .env
# Editar .env con tu API key
```

### 2. Ejecutar

```bash
python app.py
```

### 3. Usar

```
¿Qué quieres hacer?
  1. Crear proyecto nuevo
  2. Trabajar en repo Git existente

> 1

¿Nombre del proyecto? mi-app

✅ Workspace creado en ./projects/mi-app

👤 Tú: Crea una app web con React y Node que tenga login y dashboard

🤖 [El agente trabaja...]

🌐 Tu app está en: http://localhost:3000
```

---

## 📊 Resumen

| Característica | Incluido |
|----------------|----------|
| Crear proyectos nuevos | ✅ |
| Clonar repos existentes | ✅ |
| Analizar código existente | ✅ |
| Instalar dependencias | ✅ |
| Crear/editar código | ✅ |
| Ejecutar comandos | ✅ |
| Ver en navegador | ✅ |
| Crear PRs en GitHub | ✅ |
| Seguir flujo paso a paso | ✅ |
| No tocar lo que funciona | ✅ |
| Mostrar costo de sesión | ✅ |

---

*Arquitectura basada en OpenHands SDK oficial*
