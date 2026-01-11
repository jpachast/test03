# 🛠️ PLAN: Crear Chat 100% Idéntico a OpenHands

## 📋 ¿Qué se necesita?

### Componentes Requeridos:

| # | Componente | ¿Lo tenemos? | ¿Qué hacer? |
|---|------------|--------------|-------------|
| 1 | Prompts (.j2) | ✅ Sí | Ya descargados en `/prompts` |
| 2 | SDK de OpenHands | ❌ No | Instalar `openhands-sdk` |
| 3 | Tools (terminal, file_editor, etc.) | ❌ No | Vienen con `openhands-tools` |
| 4 | LLM (Gemini 2.5 Pro) | ❌ No | Configurar API key |
| 5 | Workspace (donde ejecuta) | ❌ No | Configurar directorio |
| 6 | Frontend/UI | ❌ No | Usar CLI o crear UI |

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### Fase 1: Instalación (5 minutos)

```bash
# Instalar los paquetes de OpenHands
pip install openhands-sdk      # Core del SDK
pip install openhands-tools    # Tools (terminal, file_editor, etc.)
```

### Fase 2: Configuración (10 minutos)

```bash
# Configurar API Key de Gemini
export LLM_API_KEY="tu-api-key-de-google"
export LLM_MODEL="gemini/gemini-2.5-pro"
```

### Fase 3: Crear el Chat (el código)

```python
# chat_openhands.py

import os
from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool

# 1. Configurar LLM
llm = LLM(
    model=os.getenv("LLM_MODEL", "gemini/gemini-2.5-pro"),
    api_key=os.getenv("LLM_API_KEY"),
)

# 2. Configurar Agent con Tools
agent = Agent(
    llm=llm,
    tools=[
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
    ],
)

# 3. Crear Conversación
workspace = os.getcwd()  # Directorio de trabajo
conversation = Conversation(agent=agent, workspace=workspace)

# 4. Loop del Chat
while True:
    user_input = input("\n👤 Tú: ")
    if user_input.lower() in ['exit', 'salir', 'quit']:
        break
    
    conversation.send_message(user_input)
    conversation.run()
```

### Fase 4: Ejecutar

```bash
python chat_openhands.py
```

---

## 📊 ¿Qué incluye el SDK automáticamente?

Cuando instalas `openhands-sdk`, ya viene TODO incluido:

| Componente | Incluido | Notas |
|------------|----------|-------|
| System Prompt | ✅ | `system_prompt.j2` y todos los demás |
| Security Policy | ✅ | `security_policy.j2` |
| Risk Assessment | ✅ | `security_risk_assessment.j2` |
| Model Specific | ✅ | `google_gemini.j2`, etc. |
| Tools | ✅ | Con `openhands-tools` |
| Loop de Ejecución | ✅ | Action → Observation → Decision |
| Stuck Detector | ✅ | Detecta cuando se atasca |
| Context Condenser | ✅ | Maneja contexto largo |

**Los archivos .j2 que descargamos son de REFERENCIA.** El SDK ya los tiene internamente.

---

## 🎯 Resumen: ¿Qué hay que hacer?

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   PASO 1: pip install openhands-sdk openhands-tools             │
│                                                                 │
│   PASO 2: export LLM_API_KEY="tu-key"                           │
│           export LLM_MODEL="gemini/gemini-2.5-pro"              │
│                                                                 │
│   PASO 3: Crear archivo Python con el código del chat           │
│                                                                 │
│   PASO 4: python chat_openhands.py                              │
│                                                                 │
│   ¡LISTO! Chat 100% idéntico a OpenHands                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ❓ Preguntas Frecuentes

### ¿Necesito usar los archivos .j2 que descargamos?
**NO.** El SDK ya los tiene. Los descargamos solo como referencia/documentación.

### ¿Necesito crear prompts personalizados?
**NO.** El SDK usa los prompts oficiales automáticamente.

### ¿Puedo agregar mis propios prompts?
**SÍ.** Puedes usar `AgentContext` con `system_message_suffix` para agregar instrucciones adicionales.

### ¿Funciona igual que OpenHands Cloud?
**SÍ.** El SDK es el mismo que usa OpenHands Cloud. La única diferencia es el modelo LLM (Gemini vs Claude).

---

## 📁 Estructura Final del Proyecto

```
mi-chat-openhands/
├── chat_openhands.py      # El código del chat
├── .env                   # Variables de entorno (API keys)
└── workspace/             # Donde el agente trabaja
```

---

## ⏱️ Tiempo Estimado

| Tarea | Tiempo |
|-------|--------|
| Instalar paquetes | 2 min |
| Configurar API key | 3 min |
| Crear archivo Python | 5 min |
| Probar | 5 min |
| **TOTAL** | **~15 minutos** |

---

*Este plan te da un chat 100% idéntico a OpenHands usando el SDK oficial.*
