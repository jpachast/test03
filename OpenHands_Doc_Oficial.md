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
