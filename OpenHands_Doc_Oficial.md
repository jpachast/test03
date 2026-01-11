# 📚 Documentación Completa y Oficial de OpenHands

> Documento basado 100% en la documentación oficial de OpenHands (docs.openhands.dev).
> Sin suposiciones, sin criterio propio, solo información verificada.

---

## 📋 Índice

1. [¿Qué es OpenHands?](#qué-es-openhands)
2. [Productos y Versiones Oficiales](#productos-y-versiones-oficiales)
3. [Arquitectura de 4 Paquetes](#arquitectura-de-4-paquetes)
4. [Componentes del SDK](#componentes-del-sdk)
5. [Sistema de Herramientas (Tools)](#sistema-de-herramientas-tools)
6. [Sistema de Seguridad](#sistema-de-seguridad)
7. [Sistema de Skills (Contexto)](#sistema-de-skills-contexto)
8. [Context Condenser](#context-condenser)
9. [Flujo de Ejecución Real](#flujo-de-ejecución-real)
10. [Estados de Conversación](#estados-de-conversación)
11. [Integraciones Cloud](#integraciones-cloud)
12. [Configuración y Setup](#configuración-y-setup)
13. [Troubleshooting Oficial](#troubleshooting-oficial)
14. [Best Practices para Prompts](#best-practices-para-prompts)
15. [API Reference](#api-reference)

---

## 🎯 ¿Qué es OpenHands?

Según la documentación oficial:

> "OpenHands is a community focused on AI-driven development"

**OpenHands NO es una IA.** Es un **framework/orquestador** que:
- Permite definir agentes en código
- Es agnóstico al modelo LLM
- Usa **LiteLLM** internamente para conectar con cualquier proveedor

---

## 🏢 Productos y Versiones Oficiales

### 1. OpenHands Software Agent SDK
**Fuente:** La librería Python que contiene toda la tecnología de agentes.

```bash
pip install openhands-sdk openhands-tools
```

- Define agentes en código
- Corre localmente o escala a miles de agentes en la nube
- **Código fuente:** https://github.com/All-Hands-AI/agent-sdk/

### 2. OpenHands CLI
La forma más fácil de empezar. Similar a Claude Code o Codex.

```bash
# Instalación
uv tool install openhands --python 3.12

# Lanzar
openhands serve
openhands serve --gpu        # Con GPU
openhands serve --mount-cwd  # Montar directorio actual
```

### 3. OpenHands Local GUI
GUI para correr agentes en tu laptop.
- REST API incluida
- Aplicación React de una página
- Similar a Devin o Jules

```bash
docker run -it --rm --pull=always \
  -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.openhands.dev/openhands/runtime:1.1-nikolaik \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.openhands:/.openhands \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  docker.openhands.dev/openhands/openhands:1.1
```

### 4. OpenHands Cloud
Deployment comercial en infraestructura hospedada (app.all-hands.dev).

**Características exclusivas de Cloud:**
- Integraciones profundas con GitHub, GitLab, Bitbucket
- Integraciones con Slack, Jira, Linear
- Soporte multi-usuario
- RBAC y permisos
- Colaboración (compartir conversaciones)
- Reportes de uso
- Enforcement de presupuesto

### 5. OpenHands Enterprise
Self-hosted en tu propio VPC vía Kubernetes.
- Source-available (código visible en directorio enterprise/)
- Requiere licencia para uso mayor a un mes
- Soporte extendido y acceso al equipo de investigación

---

## 🏗️ Arquitectura de 4 Paquetes

Según la documentación oficial del SDK:

| Paquete | Qué Hace | Cuándo Lo Necesitas |
|---------|----------|---------------------|
| **openhands.sdk** | Core agent framework + clases base de workspace | Siempre (requerido) |
| **openhands.tools** | Herramientas pre-construidas (bash, file editing, etc.) | Opcional |
| **openhands.workspace** | Implementaciones extendidas de workspace (Docker, remoto) | Opcional |
| **openhands.agent_server** | Servidor API multi-usuario | Opcional |

### Dos Modos de Deployment

#### Modo 1: Desarrollo Local
```bash
pip install openhands-sdk openhands-tools
```
- LocalWorkspace incluido en SDK
- Todo corre en un proceso
- Sin Docker requerido

#### Modo 2: Producción / Sandboxed
```bash
pip install openhands-sdk openhands-tools openhands-workspace openhands-agent-server
```
- RemoteWorkspace auto-spawn de agent-server en containers
- Ejecución sandboxed por seguridad
- Soporte multi-usuario y Kubernetes

---

## 🧩 Componentes del SDK

Según openhands-sdk/openhands/sdk/:

| Componente | Propósito | Código Fuente |
|------------|-----------|---------------|
| **Agent** | Loop de razonamiento-acción | openhands.sdk.agent |
| **Conversation** | Estado y ciclo de vida | openhands.sdk.conversation |
| **LLM** | Interface agnóstica con retry/telemetría | openhands.sdk.llm |
| **Tool System** | Action, Observation, Tool, Executor + MCP | openhands.sdk.tool |
| **Events** | Framework de eventos tipados | openhands.sdk.event |
| **Workspace** | LocalWorkspace, RemoteWorkspace | openhands.sdk.workspace |
| **Skill** | Prompts con triggers | openhands.sdk.context.skills |
| **Condenser** | Compresión de historial | openhands.sdk.context.condenser |
| **Security** | Evaluación de riesgo | openhands.sdk.security |

---

## 🔧 Sistema de Herramientas (Tools)

### Patrón Action/Observation/Executor

```
Action → Executor → Observation
```

| Componente | Propósito | Requisitos |
|------------|-----------|------------|
| **Action** | Parámetros del LLM | Extiende Action, propiedad visualize |
| **Observation** | Output estructurado | Extiende Observation, to_llm_content |
| **ToolExecutor** | Lógica de negocio | Implementa __call__() |
| **ToolDefinition** | Une todo | create() method |

### Tool Annotations (MCP Spec)

| Campo | Significado |
|-------|-------------|
| readOnlyHint | No modifica estado |
| destructiveHint | Puede borrar/sobreescribir |
| idempotentHint | Llamadas repetidas seguras |
| openWorldHint | Interactúa fuera del dominio |

### Herramientas Pre-construidas Oficiales

- TerminalTool - Ejecución de bash
- FileEditorTool - Ver/editar archivos
- TaskTrackerTool - Gestión de tareas
- glob - Búsqueda de archivos
- grep - Búsqueda en contenido
- think - Razonamiento sin actuar
- finish - Terminar conversación

---

## 🔐 Sistema de Seguridad

### Niveles de Riesgo (SecurityRisk)

| Nivel | Características | Ejemplos |
|-------|-----------------|----------|
| **LOW** | Read-only | Lectura de archivos, listado |
| **MEDIUM** | Modifica datos | Edición, crear archivos |
| **HIGH** | Peligroso | Borrado, comandos sistema |
| **UNKNOWN** | No analizado | Comandos complejos |

### Security Analyzers

| Analyzer | Comportamiento |
|----------|----------------|
| **LLMSecurityAnalyzer** | Extrae security_risk de argumentos |
| **NoOpSecurityAnalyzer** | Siempre retorna UNKNOWN |

### Confirmation Policies

| Policy | Comportamiento |
|--------|----------------|
| **AlwaysConfirm** | Confirmación para TODAS las acciones |
| **NeverConfirm** | Nunca requiere confirmación |
| **ConfirmRisky** | Basada en riesgo (configurable) |

### Reglas ConfirmRisky (threshold=HIGH default)

| Riesgo | confirm_unknown=True | confirm_unknown=False |
|--------|---------------------|----------------------|
| LOW | ✅ Permitir | ✅ Permitir |
| MEDIUM | ✅ Permitir | ✅ Permitir |
| HIGH | 🔒 Confirmar | 🔒 Confirmar |
| UNKNOWN | 🔒 Confirmar | ✅ Permitir |

---

## 📚 Sistema de Skills

### Tipos de Skills

| Tipo | Trigger | Descripción |
|------|---------|-------------|
| **Repository** | None (siempre) | AGENTS.md, .cursorrules, .openhands/skills/*.md |
| **Knowledge** | KeywordTrigger | Se activan con keywords |
| **Task** | TaskTrigger | Con inputs de usuario |

### Formato de Skill

```yaml
---
name: skill_name
trigger:
  type: keyword
  keywords: ["pattern1", "pattern2"]
---

# Contenido del skill
Instrucciones para el agente.
```

### AgentContext

```python
agent_context = AgentContext(
    skills=[
        Skill(name="repo.md", content="...", trigger=None),
        Skill(name="keyword", content="...", 
              trigger=KeywordTrigger(keywords=["palabra"])),
    ],
    system_message_suffix="Texto al system prompt",
    user_message_suffix="Texto a cada mensaje",
    load_public_skills=True,
)
```

---

## 🗜️ Context Condenser

### Propósito
Cuando el historial excede un límite:
1. Mantiene mensajes recientes intactos
2. Preserva información clave
3. Resume contenido antiguo usando LLM

### Beneficios Oficiales
- Hasta 2x reducción en costos de API
- Tiempos de respuesta consistentes
- Rendimiento equivalente o mejor

### Configuración

```python
condenser = LLMSummarizingCondenser(
    llm=llm.model_copy(update={"usage_id": "condenser"}),
    max_size=10,
    keep_first=2
)
agent = Agent(llm=llm, tools=tools, condenser=condenser)
```

---

## 🔄 Flujo de Ejecución Real

### Agent.step() Oficial

> "Taking a step in the conversation:
> 1. Making a LLM call
> 2. Executing the tool
> 3. Updating conversation state with LLM calls (role=assistant) 
>    and tool results (role=tool)
> 4.1 If finished → execution_status = FINISHED
> 4.2 Otherwise → Conversation kicks off next step"

### Flujo Completo

```
1. conversation.send_message("...")
2. conversation.run() inicia loop
3. Agent.step():
   a. Llamada LLM
   b. Ejecuta tool si aplica
   c. Actualiza estado
   d. FINISHED o continúa
4. Loop hasta FINISHED o max_iterations
```

---

## 📊 Estados de Conversación

### ConversationExecutionStatus (Enum)

| Estado | Descripción |
|--------|-------------|
| IDLE | Esperando input |
| RUNNING | Ejecutando |
| FINISHED | Terminado |
| PAUSED | Pausado |
| WAITING_FOR_CONFIRMATION | Esperando confirmación |
| STUCK | Atascado |
| ERROR | Error |
| DELETING | Eliminándose |

### Stuck Detector

Detecta:
- Ciclos action-observation repetitivos
- Ciclos action-error repetitivos
- Monólogo del agente
- Patrones alternantes
- Errores de context window

---

## ☁️ Integraciones Cloud

### GitHub
- Label openhands en issues → trabaja automáticamente
- Mencionar @openhands en comentarios
- Abre PRs automáticamente

### GitLab
- Label openhands en issues
- @openhands en merge requests
- Webhook automático (Premium/Ultimate)

### Otras
- Slack, Jira, Linear, Bitbucket

---

## ⚙️ Setup

### Requisitos
- MacOS/Linux/Windows+WSL
- Docker Desktop
- Mínimo 4GB RAM

### Proveedores LLM

| Proveedor | Config |
|-----------|--------|
| OpenHands LLM | app.all-hands.dev |
| Anthropic | console.anthropic.com |
| OpenAI | platform.openai.com |
| Google | aistudio.google.com |
| Ollama/LM Studio | Cualquier API key |

---

## 🔧 Troubleshooting

### Docker client failed
- Verificar Docker instalado
- docker ps debe funcionar
- Settings > Advanced > Allow default Docker socket

### Permission Denied
```bash
sudo chown <user>:<user> ~/.openhands
sudo chmod 777 ~/.openhands
```

### ConnectTimeout (Linux)
```bash
--network host
-e SANDBOX_USE_HOST_NETWORK=true
```

---

## 💡 Best Practices Prompts

### Buenos ✅
- Concretos: "Add function calculate_average in utils/math.py"
- Location-specific: "Fix TypeError in UserProfile.tsx line 42"
- Scoped: Una feature, ~100 líneas

### Malos ❌
- "Make the code better" (vago)
- "Rewrite entire backend" (fuera de scope)
- "Find the bug somewhere" (sin especificidad)

---

## 📖 API Reference

### Agent
```python
agent = Agent(
    llm=llm,
    tools=[Tool(name="TerminalTool")],
    agent_context=agent_context,
    condenser=condenser
)
```

### Conversation
```python
conv = Conversation(agent=agent, workspace="./")
conv.send_message("Hello!")
conv.run()
conv.set_confirmation_policy(ConfirmRisky())
conv.pause()
conv.close()
```

---

## 📚 Recursos Oficiales

- Docs: https://docs.openhands.dev/
- SDK: https://docs.openhands.dev/sdk
- GitHub: https://github.com/All-Hands-AI/OpenHands
- Agent SDK: https://github.com/All-Hands-AI/agent-sdk
- Skills: https://github.com/OpenHands/skills
- Cloud: https://app.all-hands.dev
- Slack: https://openhands.dev/joinslack

---

*Información 100% de docs.openhands.dev y código fuente verificado.*

---

## 🎯 CÓMO OPENHANDS CONTROLA A LA IA (Mecanismos Reales)

Esta sección documenta los **mecanismos exactos** que usa OpenHands para que el agente no se desvíe, no invente, y siga el flujo correcto.

### 1️⃣ System Prompt Estructurado y Rígido

El archivo `system_prompt.j2` define comportamiento con secciones específicas:

```
<ROLE>
* Your primary role is to assist users by executing commands, 
  modifying code, and solving technical problems effectively.
* You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question like "why is X happening", 
  don't try to fix the problem. Just give an answer to the question.
</ROLE>
```

**Efecto:** Le dice exactamente QUÉ hacer y QUÉ NO hacer.

---

### 2️⃣ Workflow de Resolución de Problemas Obligatorio

```
<PROBLEM_SOLVING_WORKFLOW>
1. EXPLORATION: Thoroughly explore relevant files and understand 
   the context before proposing solutions
2. ANALYSIS: Consider multiple approaches and select the most promising one
3. TESTING: Create tests to verify issues before implementing fixes
4. IMPLEMENTATION: Make focused, minimal changes to address the problem
5. VERIFICATION: Test your implementation thoroughly
</PROBLEM_SOLVING_WORKFLOW>
```

**Efecto:** El agente DEBE seguir estos 5 pasos en orden. No puede saltarse a "implementar" sin primero "explorar".

---

### 3️⃣ Restricciones Explícitas del Sistema de Archivos

```
<FILE_SYSTEM_GUIDELINES>
* When a user provides a file path, do NOT assume it's relative 
  to the current working directory. First explore the file system 
  to locate the file before working on it.
* NEVER create multiple versions of the same file with different 
  suffixes (e.g., file_test.py, file_fix.py)
* Always modify the original file directly when making changes
</FILE_SYSTEM_GUIDELINES>
```

**Efecto:** Previene que el agente cree archivos basura o asuma rutas.

---

### 4️⃣ Sistema de Memoria Persistente (Skills)

```
<MEMORY>
* Use AGENTS.md under the repository root as your persistent memory 
  for repository-specific knowledge and context.
* Add important insights, patterns, and learnings to this file 
  to improve future task performance.
</MEMORY>
```

**Efecto:** El agente LEE contexto antes de actuar, no inventa.

---

### 5️⃣ Política de Seguridad con 3 Niveles

```
# 🔐 Security Policy

## OK to do without Explicit User Consent
- Download and run code from a repository specified by a user
- Install and run popular packages from pypi, npm

## Do only with Explicit User Consent  
- Upload code to anywhere other than the original location
- Upload API keys or tokens

## Never Do
- Never perform any illegal activities
- Never run software to mine cryptocurrency
```

**Efecto:** Límites claros de lo que puede y no puede hacer.

---

### 6️⃣ Evaluación de Riesgo por Acción

```
# Security Risk Policy
When using tools that support security_risk parameter:

- LOW: Read-only actions (viewing files, calculations)
- MEDIUM: Container-scoped edits (modify workspace, install packages)
- HIGH: Data exfiltration, privilege breaks, sending secrets out

**Global Rules**
- Always escalate to HIGH if sensitive data leaves the environment.
```

**Efecto:** Cada acción DEBE ser clasificada con un nivel de riesgo.

---

### 7️⃣ Control de Git y PRs

```
<VERSION_CONTROL>
* Exercise caution with git operations. Do NOT make potentially 
  dangerous changes (pushing to main, deleting repos) unless 
  explicitly asked.
</VERSION_CONTROL>

<PULL_REQUESTS>
* Do not push to remote branch and/or start PR unless explicitly asked
* Create only ONE PR per session/issue
</PULL_REQUESTS>
```

**Efecto:** No hace cambios permanentes sin confirmación explícita.

---

### 8️⃣ Troubleshooting Estructurado

```
<TROUBLESHOOTING>
* If you've made repeated attempts but tests still fail:
  1. Step back and reflect on 5-7 different possible sources
  2. Assess the likelihood of each possible cause
  3. Methodically address the most likely causes
  4. Explain your reasoning process to the user
* When you run into any major issue while executing a plan, 
  don't try to directly work around it. Instead, propose a new 
  plan and confirm with the user before proceeding.
</TROUBLESHOOTING>
```

**Efecto:** Si se atasca, DEBE parar y pedir ayuda, no inventar soluciones.

---

### 9️⃣ Tools Limitadas (No puede hacer lo que quiera)

El agente SOLO puede usar las herramientas definidas:

| Tool | Qué hace | Restricción |
|------|----------|-------------|
| terminal | Ejecutar bash | Solo comandos, ve output real |
| file_editor | Ver/editar archivos | Solo en workspace |
| browser | Navegar web | Ve página real, no imagina |
| task_tracker | Gestionar tareas | Sigue la lista |
| think | Razonar | Sin efecto en sistema |
| finish | Terminar | Señala fin |

**Efecto:** Si no hay tool para algo → NO PUEDE HACERLO.

---

### 🔟 Loop Action → Observation → Decision

```python
# El ciclo real en Agent.step():
1. LLM decide acción (ej: terminal("ls -la"))
2. Executor EJECUTA la acción
3. Observation = resultado REAL (no imaginado)
4. LLM VE el resultado y decide siguiente acción
5. Repeat hasta FINISHED
```

**Efecto:** El agente VE resultados reales, no puede "soñar" que funcionó.

---

## 📊 Resumen: Por Qué NO Se Desvía

| Mecanismo | Cómo Previene Desviación |
|-----------|-------------------------|
| **System Prompt rígido** | Define rol exacto, no puede interpretarlo diferente |
| **Workflow obligatorio** | EXPLORATION → ANALYSIS → TESTING → IMPLEMENTATION |
| **File System Guidelines** | No crea archivos basura, explora antes de asumir |
| **Memory/Skills** | Lee contexto del repo, no inventa |
| **Security Policy** | Límites claros: OK / Con permiso / Nunca |
| **Risk Assessment** | Cada acción clasificada LOW/MEDIUM/HIGH |
| **Version Control rules** | No push sin permiso explícito |
| **Troubleshooting rules** | Si falla, para y pregunta |
| **Tools limitadas** | Solo puede usar herramientas definidas |
| **Loop real** | VE resultados reales, no imagina |

---

## 🔄 Flujo Real Cuando Tú Escribes un Mensaje

```
TÚ: "crea un login con react"
         ↓
┌─────────────────────────────────────────────────────────┐
│ 1. SYSTEM PROMPT se carga con todas las reglas         │
│    - ROLE, MEMORY, FILE_SYSTEM_GUIDELINES, etc.        │
│    - Security Policy                                    │
│    - Risk Assessment rules                              │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. TOOLS disponibles se inyectan                       │
│    - terminal, file_editor, browser, task_tracker...   │
│    - El LLM SOLO puede llamar estas funciones          │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. LLM recibe: [System Prompt] + [Tools] + [Tu mensaje]│
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. LLM sigue PROBLEM_SOLVING_WORKFLOW:                 │
│    a. EXPLORATION: terminal("ls -la"), file_editor(view)│
│    b. ANALYSIS: think("el usuario quiere X, Y, Z")     │
│    c. TESTING/IMPLEMENTATION: crea archivos            │
│    d. VERIFICATION: ejecuta, ve resultado real         │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Si algo falla → TROUBLESHOOTING rules:              │
│    - Para, reflexiona, propone nuevo plan              │
│    - NO inventa soluciones                             │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Cuando termina → finish()                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 La Clave: Ejecución Real, No Imaginación

```
INCORRECTO (lo que haría una IA sin control):
  IA: "He creado el archivo login.jsx con el siguiente código..."
  → Puede estar inventando, no sabes si realmente lo hizo

CORRECTO (lo que hace OpenHands):
  1. IA llama: file_editor(command="create", path="login.jsx", content="...")
  2. SISTEMA ejecuta el comando
  3. Observation: "File created successfully at login.jsx"
  4. IA VE la confirmación real
  5. IA puede verificar: file_editor(command="view", path="login.jsx")
  6. IA VE el contenido real del archivo
```

**El agente está OBLIGADO a ver resultados reales.** No puede decir "funcionó" sin haberlo ejecutado y visto el output.


---

## 🔧 FUNCIONALIDADES ADICIONALES (Lo que faltaba)

### 1️⃣ MCP (Model Context Protocol)

Permite conectar OpenHands con servidores externos de herramientas.

```python
mcp_config = {
    "mcpServers": {
        "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
        }
    }
}

agent = Agent(llm=llm, tools=tools, mcp_config=mcp_config)
```

**Soporte por plataforma:**
| Plataforma | Config |
|------------|--------|
| CLI | ~/.openhands/mcp.json |
| SDK | Programático |
| Local GUI | Settings UI |
| Cloud | Cloud UI settings |

---

### 2️⃣ Sub-Agent Delegation

Un agente puede crear sub-agentes y delegarles tareas en paralelo.

```python
# El agente usa:
{"command": "spawn", "ids": ["research", "implementation"]}

# Luego delega:
{
    "command": "delegate",
    "tasks": {
        "research": "Find best practices for async code",
        "implementation": "Refactor the MyClass class"
    }
}
```

**Características:**
- Ejecución en paralelo con threads
- Cada sub-agente tiene su propio contexto
- Resultados consolidados al terminar

---

### 3️⃣ Iterative Refinement

Patrón donde múltiples agentes trabajan en loop de feedback:

```
1. Agente de refactoring → hace la tarea
2. Agente de crítica → evalúa calidad (0-100)
3. Si score < 90% → agente de refactoring intenta de nuevo con feedback
4. Repeat hasta PASS
```

---

### 4️⃣ Secret Registry

Manejo seguro de secretos en comandos:

```python
conversation.update_secrets({
    "SECRET_TOKEN": "my-secret-value",
    "API_KEY": MySecretSource()  # callable
})

# Cuando el agente ejecuta:
# terminal("echo $SECRET_TOKEN")
# → El sistema inyecta el valor como env var
# → En el output se ve: <secret-hidden>
```

**Características:**
- Detección automática de referencias a secretos
- Inyección como variables de entorno
- Masking en outputs para prevenir exposición

---

### 5️⃣ Persistencia de Conversaciones

Guardar y restaurar estado entre sesiones:

```python
conversation = Conversation(
    agent=agent,
    workspace=cwd,
    persistence_dir="./.conversations",
    conversation_id=uuid.uuid4(),
)
```

**Estructura:**
```
.conversations/
├── <conversation_id>/
│   ├── base_state.json    # Estado base
│   └── events/            # Eventos individuales
│       ├── event-00000-abc.json
│       └── event-00001-def.json
```

**Qué se persiste:**
- Message History
- Agent Configuration
- Execution State
- Tool Outputs
- Statistics
- Activated Skills
- Secrets

---

### 6️⃣ Stuck Detector

Detecta cuando el agente está atascado:

| Patrón | Descripción |
|--------|-------------|
| action_observation | Ciclos repetitivos de acción-observación |
| action_error | Misma acción, mismo error |
| monologue | Agente hablando solo sin input |
| alternating_pattern | Patrones alternantes repetitivos |
| context_window | Errores de memoria |

**Configuración:**
```python
conversation = Conversation(
    agent=agent,
    stuck_detection=True,
    stuck_detection_thresholds={
        'action_observation': 3,
        'action_error': 4,
        'monologue': 3,
        'alternating_pattern': 3
    }
)
```

---

### 7️⃣ Callbacks y Events

Sistema de callbacks para recibir eventos:

```python
def conversation_callback(event: Event):
    if isinstance(event, LLMConvertibleEvent):
        llm_messages.append(event.to_llm_message())

conversation = Conversation(
    agent=agent,
    callbacks=[conversation_callback],
    token_callbacks=[on_token],  # Para streaming
)
```

---

### 8️⃣ Metrics Tracking

Seguimiento de costos y tokens:

```python
stats = conversation.conversation_stats.get_combined_metrics()
print(f"Cost: ${stats.accumulated_cost:.6f}")
print(f"Prompt Tokens: {stats.accumulated_token_usage.prompt_tokens}")
print(f"Completion Tokens: {stats.accumulated_token_usage.completion_tokens}")

# Por usage_id
for usage_id, metrics in stats.usage_to_metrics.items():
    print(f"{usage_id}: ${metrics.accumulated_cost:.6f}")
```

---

### 9️⃣ Visualizer

Visualización de eventos en consola:

```python
from openhands.sdk import DefaultConversationVisualizer, DelegationVisualizer

# Visualización por defecto con Rich
conversation = Conversation(
    agent=agent,
    visualizer=DefaultConversationVisualizer(
        highlight_regex={"error": "red", "success": "green"},
        skip_user_messages=False
    )
)

# Para delegation
conversation = Conversation(
    agent=agent,
    visualizer=DelegationVisualizer(name="MainAgent")
)
```

---

### 🔟 ask_agent() - Preguntas Stateless

Preguntar algo al agente sin afectar la conversación:

```python
# Thread-safe, no modifica estado
response = conversation.ask_agent("What's 2+2?")
# La pregunta NO queda en el historial
# Útil mientras conversation.run() está ejecutando
```

---

## ✅ CHECKLIST: ¿Está completo?

| Característica | Documentado |
|---------------|-------------|
| 5 Productos (SDK, CLI, GUI, Cloud, Enterprise) | ✅ |
| Arquitectura 4 Paquetes | ✅ |
| 9 Componentes del SDK | ✅ |
| Sistema de Tools + MCP | ✅ |
| Sistema de Seguridad (Risk, Analyzers, Policies) | ✅ |
| Sistema de Skills (Repo, Knowledge, Task) | ✅ |
| Context Condenser | ✅ |
| 8 Estados de Conversación | ✅ |
| 10 Mecanismos de Control del Agente | ✅ |
| Integraciones Cloud (GitHub, GitLab, Slack, Jira) | ✅ |
| MCP (Model Context Protocol) | ✅ |
| Sub-Agent Delegation | ✅ |
| Iterative Refinement | ✅ |
| Secret Registry | ✅ |
| Persistencia de Conversaciones | ✅ |
| Stuck Detector | ✅ |
| Callbacks y Events | ✅ |
| Metrics Tracking | ✅ |
| Visualizer | ✅ |
| ask_agent() Stateless | ✅ |
| Troubleshooting | ✅ |
| Best Practices Prompts | ✅ |
| API Reference | ✅ |

---

*Documento actualizado con todas las funcionalidades de OpenHands según docs.openhands.dev*

---

## 🚨 LO QUE FALTABA (Completando al 100%)

### 📄 Sistema de Prompts Completo

**11 archivos de prompts que trabajan juntos:**

```
prompts/
├── system_prompt.j2              ← PRINCIPAL (siempre se usa)
│   ├── {% include 'self_documentation.j2' %}
│   ├── {% include security_policy_filename %}
│   ├── {% include 'security_risk_assessment.j2' %}  (condicional)
│   └── {% include "model_specific/..." %}  (condicional)
│
├── system_prompt_interactive.j2  ← Modo interactivo
├── system_prompt_long_horizon.j2 ← Tareas largas
├── system_prompt_planning.j2     ← Agente de planificación
├── system_prompt_tech_philosophy.j2
│
├── security_policy.j2            ← Se INCLUYE en principal
├── security_risk_assessment.j2   ← Se INCLUYE (condicional)
├── self_documentation.j2         ← Se INCLUYE para auto-docs
│
├── in_context_learning_example.j2
├── in_context_learning_example_suffix.j2
│
└── model_specific/               ← Ajustes por modelo
    ├── gpt.j2
    ├── claude.j2
    └── gpt/gpt-5-codex.j2
```

---

### 🔧 LLM Configuration Completa

```python
from openhands.sdk import LLM
from pydantic import SecretStr

llm = LLM(
    model="anthropic/claude-sonnet-4-5-20250929",
    api_key=SecretStr("sk-..."),
    base_url=None,  # Opcional para custom endpoints
    temperature=0.1,
    timeout=120,
    num_retries=5,
    usage_id="agent",  # Para tracking de costos
    input_cost_per_token=0.00001,  # Custom pricing
    output_cost_per_token=0.00003,
    disable_vision=False,  # True para ahorrar costos
)
```

**Configuración por Environment Variables:**
```bash
export LLM_MODEL="anthropic/claude-sonnet-4-5-20250929"
export LLM_API_KEY="sk-..."
export LLM_USAGE_ID="primary"
export LLM_TIMEOUT="120"
export LLM_NUM_RETRIES="5"
```

---

### 📊 100+ Proveedores LLM Soportados

Via LiteLLM:
- OpenAI, Anthropic, Google, Azure, AWS Bedrock
- Groq, OpenRouter, Moonshot
- Ollama, SGLang, vLLM, LM Studio (locales)

**Ejemplo AWS Bedrock:**
```python
llm = LLM(model="bedrock/anthropic.claude-3-sonnet-20240229-v1:0")
# Necesita: pip install boto3
# export AWS_BEARER_TOKEN_BEDROCK="..."
```

---

### 🖼️ Soporte de Imágenes (Vision)

```python
from openhands.sdk import ImageContent, Message, TextContent

# Verificar soporte
assert llm.vision_is_active(), "Model does not support vision"

# URL HTTP
message = Message(
    role="user",
    content=[
        TextContent(text="What do you see?"),
        ImageContent(image_urls=["https://example.com/image.png"]),
    ],
)

# Base64
import base64
with open("image.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
ImageContent(image_urls=[f"data:image/png;base64,{img_b64}"])
```

---

### 🔀 Parallel Tool Calling

El SDK soporta llamadas paralelas de herramientas:

```python
# El LLM puede retornar múltiples tool calls en una respuesta
# Se agrupan por llm_response_id

ActionEvent(llm_response_id="abc123", tool_call=tool1)
ActionEvent(llm_response_id="abc123", tool_call=tool2)
# → Se combinan en: Message(tool_calls=[tool1, tool2])
```

---

### 📈 Observability & Tracing (OpenTelemetry)

```bash
# Con Laminar
export LMNR_PROJECT_API_KEY="your-laminar-api-key"

# Con Honeycomb
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="https://api.honeycomb.io:443/v1/traces"
export OTEL_EXPORTER_OTLP_TRACES_HEADERS="x-honeycomb-team=YOUR_API_KEY"
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL="http/protobuf"

# Con Jaeger local
docker run -d --name jaeger -p 4317:4317 -p 16686:16686 jaegertracing/all-in-one:latest
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://localhost:4317"
```

**Qué se tracéa:**
```
conversation (session_id: uuid)
└── conversation.run
    ├── agent.step
    │   ├── llm.completion
    │   └── tool.execute ("bash", "file_editor", etc.)
    └── agent.step
        └── llm.completion
```

---

### 🛠️ Custom Tools - Cómo Crearlos

```python
from openhands.sdk import Action, Observation, ToolDefinition, ToolExecutor
from pydantic import Field

# 1. Definir Action (input)
class MyAction(Action):
    param: str = Field(description="Parámetro de entrada")

# 2. Definir Observation (output)
class MyObservation(Observation):
    result: str
    
    @property
    def to_llm_content(self):
        return [TextContent(text=self.result)]

# 3. Definir Executor (lógica)
class MyExecutor(ToolExecutor[MyAction, MyObservation]):
    def __call__(self, action: MyAction, conversation=None) -> MyObservation:
        return MyObservation(result=f"Procesado: {action.param}")

# 4. Crear ToolDefinition
class MyTool(ToolDefinition[MyAction, MyObservation]):
    @classmethod
    def create(cls, conv_state) -> list[ToolDefinition]:
        return [cls(
            description="Mi herramienta custom",
            action_type=MyAction,
            observation_type=MyObservation,
            executor=MyExecutor(),
        )]

# 5. Registrar
from openhands.sdk.tool import register_tool
register_tool("MyTool", MyTool)

# 6. Usar
agent = Agent(llm=llm, tools=[Tool(name="MyTool")])
```

---

### 🔄 Hooks System

```python
from openhands.sdk import HookConfig

hook_config = HookConfig(
    pre_action_hooks=[my_pre_hook],
    post_action_hooks=[my_post_hook],
)

conversation = Conversation(
    agent=agent,
    hook_config=hook_config,
)
```

---

### 🏗️ Workspace Types

| Tipo | Uso | Instalación |
|------|-----|-------------|
| LocalWorkspace | Desarrollo local | Incluido en SDK |
| DockerWorkspace | Sandboxed en container | openhands-workspace |
| RemoteWorkspace | Servidor remoto | openhands-workspace |
| RemoteAPIWorkspace | API hospedada | openhands-workspace |

```python
# Local (default)
conversation = Conversation(agent=agent, workspace="./")

# Docker
from openhands.workspace import DockerWorkspace
workspace = DockerWorkspace(image="python:3.12")
conversation = Conversation(agent=agent, workspace=workspace)
```

---

### 📋 Default Tools Preset

```python
from openhands.tools.preset.default import get_default_tools, get_default_agent

# Obtener tools por defecto
tools = get_default_tools(enable_browser=True)

# O el agente completo configurado
agent = get_default_agent(llm=llm, cli_mode=True)
```

**Tools incluidos por defecto:**
- TerminalTool
- FileEditorTool
- TaskTrackerTool
- think
- finish

---

### ⏸️ Pause/Resume

```python
# Pausar (desde otro thread)
conversation.pause()

# Continuar
conversation.run()

# Estados posibles
# IDLE → RUNNING → PAUSED → RUNNING → FINISHED
```

---

### 📝 Title Generation

```python
# Generar título basado en primer mensaje
title = conversation.generate_title(max_length=50)
```

---

### 🔧 Condense On Demand

```python
# Forzar condensación manualmente
conversation.condense()
```

---

### 🎛️ Agent Configuration Completa

```python
agent = Agent(
    llm=llm,
    tools=[Tool(name="TerminalTool"), Tool(name="FileEditorTool")],
    agent_context=AgentContext(
        skills=[...],
        system_message_suffix="...",
        user_message_suffix="...",
        load_public_skills=True,
    ),
    condenser=LLMSummarizingCondenser(llm=llm, max_size=10),
    mcp_config={"mcpServers": {...}},
    system_prompt_filename="system_prompt.j2",  # Cambiar prompt
    system_prompt_kwargs={"cli_mode": True},  # Variables al template
    security_policy_filename="security_policy.j2",
    filter_tools_regex=".*",  # Filtrar tools por regex
)
```

---

### 📊 Responses API (GPT-5)

Para modelos como GPT-5-Codex que usan Responses API:

```python
# Automáticamente detectado para modelos gpt-5*
llm = LLM(model="openai/gpt-5-codex")

# Usa responses() en vez de completion()
# Soporta encrypted thinking y reasoning summaries
```

---

## ✅ CHECKLIST FINAL COMPLETO

| # | Característica | ✅ |
|---|---------------|---|
| 1 | 5 Productos (SDK, CLI, GUI, Cloud, Enterprise) | ✅ |
| 2 | Arquitectura 4 Paquetes | ✅ |
| 3 | 9 Componentes del SDK | ✅ |
| 4 | Sistema de Tools + MCP | ✅ |
| 5 | Sistema de Seguridad | ✅ |
| 6 | Sistema de Skills | ✅ |
| 7 | Context Condenser | ✅ |
| 8 | 8 Estados de Conversación | ✅ |
| 9 | 10 Mecanismos de Control | ✅ |
| 10 | Integraciones Cloud | ✅ |
| 11 | MCP (Model Context Protocol) | ✅ |
| 12 | Sub-Agent Delegation | ✅ |
| 13 | Iterative Refinement | ✅ |
| 14 | Secret Registry | ✅ |
| 15 | Persistencia | ✅ |
| 16 | Stuck Detector | ✅ |
| 17 | Callbacks y Events | ✅ |
| 18 | Metrics Tracking | ✅ |
| 19 | Visualizer | ✅ |
| 20 | ask_agent() | ✅ |
| 21 | **11 Archivos de Prompts** | ✅ |
| 22 | **LLM Config Completa** | ✅ |
| 23 | **100+ Proveedores** | ✅ |
| 24 | **Vision/Imágenes** | ✅ |
| 25 | **Parallel Tool Calling** | ✅ |
| 26 | **Observability/Tracing** | ✅ |
| 27 | **Custom Tools Creation** | ✅ |
| 28 | **Hooks System** | ✅ |
| 29 | **4 Workspace Types** | ✅ |
| 30 | **Default Tools Preset** | ✅ |
| 31 | **Pause/Resume** | ✅ |
| 32 | **Title Generation** | ✅ |
| 33 | **Condense On Demand** | ✅ |
| 34 | **Agent Config Completa** | ✅ |
| 35 | **Responses API (GPT-5)** | ✅ |
| 36 | Troubleshooting | ✅ |
| 37 | Best Practices | ✅ |

---

*Documento 100% completo basado en docs.openhands.dev y código fuente oficial.*
*Total: 37 características documentadas.*

---

## 📜 SISTEMA DE PROMPTS COMPLETO DE OPENHANDS

### 🗂️ Archivos de Prompts Descargados

Los archivos originales están disponibles en la carpeta `prompts/` de este repositorio:

```
prompts/
├── system_prompt.j2                    ← PRINCIPAL (9.2KB)
├── security_policy.j2                  ← Política de seguridad (993B)
├── self_documentation.j2               ← Auto-documentación (1KB)
├── security_risk_assessment.j2         ← Evaluación de riesgo (1.2KB)
├── system_prompt_interactive.j2        ← Modo interactivo (1.4KB)
├── system_prompt_long_horizon.j2       ← Tareas largas (3KB)
├── system_prompt_planning.j2           ← Planificación (2.9KB)
├── system_prompt_tech_philosophy.j2    ← Filosofía técnica (5KB)
├── in_context_learning_example.j2      ← Ejemplos ICL (5.5KB)
├── in_context_learning_example_suffix.j2
└── model_specific/
    ├── anthropic.j2
    ├── gemini.j2
    └── openai.j2
```

---

### 🔄 EL PROMPT FINAL QUE VE EL LLM

El prompt final es la **combinación** de múltiples fuentes:

```
┌─────────────────────────────────────────────────────────────────┐
│            EL PROMPT FINAL ES LA COMBINACIÓN DE:                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. system_prompt.j2 (base)                                     │
│     └── Contiene: ROLE, MEMORY, EFFICIENCY, FILE_SYSTEM_        │
│         GUIDELINES, CODE_QUALITY, VERSION_CONTROL,              │
│         PULL_REQUESTS, PROBLEM_SOLVING_WORKFLOW,                │
│         EXTERNAL_SERVICES, ENVIRONMENT_SETUP,                   │
│         TROUBLESHOOTING, PROCESS_MANAGEMENT                     │
│                                                                 │
│  2. security_policy.j2 (incluido)                               │
│     └── {% include security_policy_filename %}                  │
│     └── Define: OK sin consentimiento, Solo con consentimiento, │
│         Nunca hacer                                             │
│                                                                 │
│  3. self_documentation.j2 (incluido)                            │
│     └── {% include 'self_documentation.j2' %}                   │
│     └── Instrucciones para consultar docs.openhands.dev         │
│                                                                 │
│  4. security_risk_assessment.j2 (si aplica)                     │
│     └── {% if llm_security_analyzer %}                          │
│     └── Define niveles: LOW, MEDIUM, HIGH                       │
│                                                                 │
│  5. model_specific/xxx.j2 (si aplica al modelo)                 │
│     └── {% include "model_specific/" ~ model_family ~ ".j2" %}  │
│     └── Ajustes específicos para GPT, Claude, Gemini, etc.      │
│                                                                 │
│  6. Skills activados (de AGENTS.md, etc.)                       │
│     └── Se cargan dinámicamente según el repositorio            │
│     └── Conocimiento específico del proyecto                    │
│                                                                 │
│  7. system_message_suffix del AgentContext                      │
│     └── agent_context.system_message_suffix                     │
│     └── Personalización adicional por el desarrollador          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 📋 CONTENIDO DE CADA ARCHIVO

#### 1️⃣ system_prompt.j2 (BASE)

Este es el prompt principal que define el comportamiento del agente:

```jinja2
You are OpenHands agent, a helpful AI assistant that can interact 
with a computer to solve tasks.

<ROLE>
* Your primary role is to assist users by executing commands, 
  modifying code, and solving technical problems effectively.
* You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question, like "why is X happening", 
  don't try to fix the problem. Just give an answer to the question.
</ROLE>

<MEMORY>
* Use AGENTS.md under the repository root as your persistent memory
* Add important insights, patterns, and learnings to this file
</MEMORY>

<EFFICIENCY>
* Each action you take is somewhat expensive
* Combine multiple actions into a single action when possible
</EFFICIENCY>

<FILE_SYSTEM_GUIDELINES>
* Do NOT assume paths are relative to current directory
* NEVER create multiple versions of same file
* Always modify original file directly
</FILE_SYSTEM_GUIDELINES>

<CODE_QUALITY>
* Write clean, efficient code with minimal comments
* Make minimal changes needed to solve the problem
</CODE_QUALITY>

<VERSION_CONTROL>
* Do NOT make dangerous changes (push to main, delete repos)
* Use git commit -a whenever possible
</VERSION_CONTROL>

<PULL_REQUESTS>
* Do not push unless explicitly asked
* Create only ONE PR per session/issue
</PULL_REQUESTS>

<PROBLEM_SOLVING_WORKFLOW>
1. EXPLORATION
2. ANALYSIS
3. TESTING
4. IMPLEMENTATION
5. VERIFICATION
</PROBLEM_SOLVING_WORKFLOW>

<SELF_DOCUMENTATION>
{% include 'self_documentation.j2' %}
</SELF_DOCUMENTATION>

<SECURITY>
{% include security_policy_filename %}
</SECURITY>

{% if llm_security_analyzer %}
<SECURITY_RISK_ASSESSMENT>
{% include 'security_risk_assessment.j2' %}
</SECURITY_RISK_ASSESSMENT>
{% endif %}

<EXTERNAL_SERVICES>...</EXTERNAL_SERVICES>
<ENVIRONMENT_SETUP>...</ENVIRONMENT_SETUP>
<TROUBLESHOOTING>...</TROUBLESHOOTING>
<PROCESS_MANAGEMENT>...</PROCESS_MANAGEMENT>

{# Incluir ajustes específicos del modelo #}
{% if model_family %}
<IMPORTANT>
{% include "model_specific/" ~ model_family ~ ".j2" %}
</IMPORTANT>
{% endif %}
```

---

#### 2️⃣ security_policy.j2

```jinja2
# 🔐 Security Policy

## OK to do without Explicit User Consent
- Download and run code from a repository specified by a user
- Open pull requests on the original repositories
- Install and run popular packages from pypi, npm
- Use APIs to work with GitHub or other platforms

## Do only with Explicit User Consent
- Upload code to anywhere other than the original location
- Upload API keys or tokens anywhere

## Never Do
- Never perform any illegal activities
- Never run software to mine cryptocurrency

## General Security Guidelines
- Only use GITHUB_TOKEN and other credentials in ways 
  the user has explicitly requested and would expect
```

---

#### 3️⃣ self_documentation.j2

```jinja2
When the user directly asks about any of the following:
- OpenHands capabilities (e.g., "can OpenHands do...", "does OpenHands have...")
- what you're able to do in second person (e.g., "are you able...", "can you...")
- how to use a specific OpenHands feature or product
- how to use the OpenHands SDK, CLI, GUI, or other OpenHands products

Get accurate information from the official OpenHands documentation 
at <https://docs.openhands.dev/>. The documentation includes:

**OpenHands SDK** (`/sdk/*`): Python library for building AI agents
**OpenHands CLI** (`/openhands/usage/run-openhands/cli-mode`)
**OpenHands GUI** (`/openhands/usage/run-openhands/local-setup`)
**OpenHands Cloud** (`/openhands/usage/run-openhands/cloud`)
**OpenHands Enterprise**: Self-hosted deployment

Always provide links to the relevant documentation pages.
```

---

#### 4️⃣ security_risk_assessment.j2

```jinja2
# Security Risk Policy
When using tools that support the security_risk parameter, 
assess the safety risk of your actions:

{% if cli_mode | default(true) %}
- **LOW**: Safe, read-only actions.
  - Viewing/summarizing content, reading project files
- **MEDIUM**: Project-scoped edits or execution.
  - Modify user project files, run project scripts/tests
- **HIGH**: System-level or untrusted operations.
  - Changing system settings, global installs, sudo commands
{% else %}
- **LOW**: Read-only actions inside sandbox.
  - Inspecting container files, calculations, viewing docs.
- **MEDIUM**: Container-scoped edits and installs.
  - Modify workspace files, install packages inside container
- **HIGH**: Data exfiltration or privilege breaks.
  - Sending secrets/local data out, privileged container ops
{% endif %}

**Global Rules**
- Always escalate to **HIGH** if sensitive data leaves the environment.
```

---

### 🔧 CÓMO SE ENSAMBLA EL PROMPT FINAL

```python
# En Agent.__init__() o antes de llamar al LLM:

from jinja2 import Environment, FileSystemLoader

# 1. Cargar el template base
env = Environment(loader=FileSystemLoader('prompts/'))
template = env.get_template('system_prompt.j2')

# 2. Preparar variables del contexto
context = {
    'security_policy_filename': 'security_policy.j2',
    'llm_security_analyzer': True,  # Si está habilitado
    'model_family': 'anthropic',    # gpt, anthropic, gemini
    'model_variant': None,          # Para sub-variantes
    'cli_mode': True,               # Afecta security_risk_assessment
}

# 3. Renderizar el template (resuelve todos los {% include %})
system_prompt = template.render(**context)

# 4. Agregar Skills activados
for skill in activated_skills:
    system_prompt += f"\n<SKILL name='{skill.name}'>\n{skill.content}\n</SKILL>"

# 5. Agregar system_message_suffix del AgentContext
if agent_context.system_message_suffix:
    system_prompt += f"\n{agent_context.system_message_suffix}"

# 6. El prompt final se envía al LLM
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_message},
]
```

---

### 📊 DIAGRAMA DEL FLUJO DE ENSAMBLAJE

```
                    ┌─────────────────────┐
                    │   system_prompt.j2  │
                    │       (BASE)        │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│security_policy.j2│ │self_documentation│ │security_risk_   │
│    (SIEMPRE)     │ │   .j2 (SIEMPRE) │ │assessment.j2    │
└────────┬────────┘  └────────┬────────┘ │ (SI ANALYZER)   │
         │                    │          └────────┬────────┘
         └────────────────────┼───────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  model_specific/    │
                    │  {model_family}.j2  │
                    │   (SI APLICA)       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SKILLS ACTIVADOS  │
                    │  (AGENTS.md, etc.)  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ system_message_     │
                    │ suffix (AgentContext│
                    └──────────┬──────────┘
                               │
                               ▼
                    ╔═════════════════════╗
                    ║  PROMPT FINAL PARA  ║
                    ║       EL LLM        ║
                    ╚═════════════════════╝
```

---

### 🎯 EJEMPLO DE PROMPT FINAL ENSAMBLADO

```
You are OpenHands agent, a helpful AI assistant...

<ROLE>
* Your primary role is to assist users by executing commands...
</ROLE>

<MEMORY>
* Use AGENTS.md under the repository root...
</MEMORY>

<EFFICIENCY>...</EFFICIENCY>
<FILE_SYSTEM_GUIDELINES>...</FILE_SYSTEM_GUIDELINES>
<CODE_QUALITY>...</CODE_QUALITY>
<VERSION_CONTROL>...</VERSION_CONTROL>
<PULL_REQUESTS>...</PULL_REQUESTS>
<PROBLEM_SOLVING_WORKFLOW>...</PROBLEM_SOLVING_WORKFLOW>

<SELF_DOCUMENTATION>
When the user directly asks about OpenHands capabilities...
Get accurate information from docs.openhands.dev...
</SELF_DOCUMENTATION>

<SECURITY>
# 🔐 Security Policy
## OK to do without Explicit User Consent
- Download and run code from a repository...
## Do only with Explicit User Consent
- Upload code to anywhere other than the original location...
## Never Do
- Never perform any illegal activities...
</SECURITY>

<SECURITY_RISK_ASSESSMENT>
# Security Risk Policy
- LOW: Read-only actions inside sandbox
- MEDIUM: Container-scoped edits and installs
- HIGH: Data exfiltration or privilege breaks
</SECURITY_RISK_ASSESSMENT>

<EXTERNAL_SERVICES>...</EXTERNAL_SERVICES>
<ENVIRONMENT_SETUP>...</ENVIRONMENT_SETUP>
<TROUBLESHOOTING>...</TROUBLESHOOTING>
<PROCESS_MANAGEMENT>...</PROCESS_MANAGEMENT>

<SKILL name='repo.md'>
[Contenido del archivo .openhands/skills/repo.md del repositorio]
</SKILL>

[system_message_suffix adicional si está configurado]
```

---

### 📁 ARCHIVOS DISPONIBLES EN ESTE REPOSITORIO

Los archivos de prompts originales están en `prompts/`:

| Archivo | Tamaño | Descripción |
|---------|--------|-------------|
| `system_prompt.j2` | 9.2KB | Prompt principal (base) |
| `security_policy.j2` | 993B | Política de seguridad |
| `self_documentation.j2` | 1KB | Auto-documentación |
| `security_risk_assessment.j2` | 1.2KB | Evaluación de riesgo |
| `system_prompt_interactive.j2` | 1.4KB | Modo interactivo |
| `system_prompt_long_horizon.j2` | 3KB | Tareas largas |
| `system_prompt_planning.j2` | 2.9KB | Planificación |
| `system_prompt_tech_philosophy.j2` | 5KB | Filosofía técnica |
| `in_context_learning_example.j2` | 5.5KB | Ejemplos ICL |
| `model_specific/anthropic.j2` | 14B | Ajustes Claude |
| `model_specific/openai.j2` | 14B | Ajustes GPT |
| `model_specific/gemini.j2` | 14B | Ajustes Gemini |

---

*Fuente: https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-sdk/openhands/sdk/agent/prompts*
