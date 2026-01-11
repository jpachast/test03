# 📚 Documentación Completa de OpenHands

> Documento exhaustivo sobre el funcionamiento interno del chat de OpenHands, su arquitectura, flujos de procesamiento, y cómo replicar un sistema similar.

---

## 📋 Índice

1. [Arquitectura del Chat de OpenHands](#arquitectura-del-chat-de-openhands)
2. [Componentes Clave del Sistema](#componentes-clave-del-sistema)
3. [Flujo del Chat](#flujo-del-chat)
4. [Patrón Action/Observation/Executor](#patrón-actionobservationexecutor)
5. [Cómo OpenHands Controla a la IA](#cómo-openhands-controla-a-la-ia)
6. [Flujo Real de Procesamiento de Peticiones](#flujo-real-de-procesamiento-de-peticiones)
7. [Manejo de Peticiones Desordenadas](#manejo-de-peticiones-desordenadas)
8. [Comparación de Modelos LLM](#comparación-de-modelos-llm)
9. [Componentes para Replicar el Sistema](#componentes-para-replicar-el-sistema)

---

## 🏗️ Arquitectura del Chat de OpenHands

OpenHands es un **framework/orquestador** que permite a agentes de IA ejecutar tareas de desarrollo. **NO tiene IA propia** - es agnóstico al modelo LLM que utilices.

### Diagrama de Alto Nivel

```
Usuario → OpenHands → LLM (el que tú elijas) → Respuesta
                ↓
         Ejecuta herramientas
         (bash, archivos, web)
```

### ¿Qué IA usa OpenHands?

OpenHands usa **LiteLLM** internamente, que es una librería que unifica la API de todos los proveedores. Por eso puede trabajar con cualquiera:

| Proveedor | Modelos | Costo |
|-----------|---------|-------|
| **OpenHands LLM** | Modelos optimizados para código (via app.all-hands.dev) | 💰 Pago |
| **Anthropic** | Claude 3.5, Claude 4 | 💰 Pago |
| **OpenAI** | GPT-4o, GPT-4, o3, o4-mini | 💰 Pago |
| **Google** | Gemini Pro, Gemini Ultra | 💰 Pago |
| **OpenRouter** | Acceso a múltiples modelos | 💰 Pago |
| **Ollama** | Llama, Mistral, Qwen, etc. | 🆓 Gratis (local) |
| **LM Studio** | Cualquier modelo GGUF | 🆓 Gratis (local) |
| **llama.cpp** | Modelos locales | 🆓 Gratis (local) |


---

## 🧩 Componentes Clave del Sistema

| Componente | Función |
|------------|---------|
| **Agent** | Bucle central de razonamiento-acción. Recibe mensaje → piensa → ejecuta herramientas → responde |
| **Conversation** | Maneja el estado de la conversación y su ciclo de vida |
| **LLM** | Interface agnóstica al modelo (Claude, GPT, Qwen, etc.) |
| **Tools** | Herramientas pre-construidas: bash, edición de archivos, navegador web, MCP |
| **Workspace** | Entorno donde se ejecutan las acciones (local, Docker, remoto) |
| **Events** | Sistema de eventos tipados (acciones, observaciones, mensajes) |
| **Condenser** | Comprime el historial para manejar límites de tokens |
| **Security** | Evalúa riesgo de acciones antes de ejecutarlas |

### Características Clave

- **Stateless**: Componentes sin estado, fácil de escalar
- **Persistable**: Las conversaciones se pueden guardar/retomar
- **Compresión de contexto**: Cuando el historial es muy largo, lo comprime automáticamente
- **Multi-modelo**: Funciona con cualquier LLM
- **Sandboxed**: Puede ejecutar código en contenedores Docker aislados


---

## 🔄 Flujo del Chat (Simplificado)

```
1. Usuario envía mensaje
2. Agent recibe mensaje + contexto (historial, herramientas disponibles)
3. Agent llama al LLM para decidir qué hacer
4. LLM responde con:
   - Texto para el usuario, O
   - Llamada a herramienta (bash, editar archivo, navegar web, etc.)
5. Si es herramienta → se ejecuta en el Workspace → resultado vuelve al Agent
6. Loop continúa hasta que Agent decide que terminó
7. Respuesta final al usuario
```

---

## ⚡ Patrón Action/Observation/Executor

Cada herramienta sigue este patrón:

```
┌─────────────────────────────────────────────────────────┐
│  Action: Define qué hacer (ej: BashAction(command="ls -la"))  │
│                           ↓                             │
│  Executor: Ejecuta la acción                            │
│                           ↓                             │
│  Observation: Resultado de la ejecución                 │
└─────────────────────────────────────────────────────────┘
```

### Ejemplo Práctico

```
Usuario: "Crea un servidor Express"
        ↓
IA piensa: "Necesito crear un archivo"
        ↓
Ejecuta: file_editor.create("server.js", código)
        ↓
Observa: "Archivo creado"
        ↓
IA piensa: "Ahora debo ejecutarlo"
        ↓
Ejecuta: terminal("node server.js")
        ↓
Observa: "Server running on port 3000"
        ↓
IA: "Listo, servidor funcionando"
```

**La IA no puede "soñar" que funcionó. VE el resultado real.**


---

## 🎮 Cómo OpenHands Controla a la IA

### El Problema que Resuelve

Las IAs tienden a:
- ❌ Inventar cosas
- ❌ Irse por las ramas
- ❌ Olvidar el objetivo
- ❌ Hacer lo que "creen" correcto

### La Solución: 7 Mecanismos de Control

#### 1. System Prompt Rígido

```
"Eres un agente de desarrollo. SOLO puedes:
- Ejecutar comandos bash
- Editar archivos
- Navegar web
NO opines. NO inventes. Ejecuta."
```

**Le quita libertad creativa, lo vuelve un ejecutor.**

#### 2. Herramientas Limitadas (Tools)

La IA **NO puede hacer lo que quiera**. Solo puede llamar funciones específicas:

| Tool | Qué hace |
|------|----------|
| `terminal` | Ejecutar bash |
| `file_editor` | Ver/editar archivos |
| `browser` | Navegar web |
| `task_tracker` | Gestionar tareas |
| `think` | Razonar sin actuar |
| `finish` | Terminar conversación |

**Si no hay tool para algo → no puede hacerlo.**

#### 3. Loop Acción → Observación → Decisión

```
Usuario: "Crea la página de login"
        ↓
Ejecuta: browser_navigate("http://localhost:3000/login")
        ↓
VE la página real → detecta errores → corrige
```

**No asume que funciona. Lo comprueba.**

#### 4. Contexto Persistente (Skills)

Archivo `.openhands/skills/repo.md` que le dice:

```markdown
- Este proyecto usa React + Node
- La base de datos es PostgreSQL
- NO uses yarn, usa npm
- Los tests van en /tests
```

**La IA lo lee SIEMPRE antes de actuar.**

#### 5. Task Tracker (Descomposición)

Para proyectos grandes:

```
Tarea: "Construir e-commerce"

Se descompone en:
☐ 1. Crear estructura del proyecto
☐ 2. Configurar base de datos
☐ 3. Crear modelo de productos
☐ 4. Crear API endpoints
☐ 5. Crear frontend
```

**La IA sigue la lista, no inventa el camino.**

#### 6. Verificación Visual (Browser)

```
IA: "Creé la página de login"
        ↓
Ejecuta: browser_navigate("http://localhost:3000/login")
        ↓
VE la página real → detecta errores → corrige
```

**No asume que funciona. Lo comprueba.**

#### 7. Seguridad (Confirmación)

Antes de acciones riesgosas:

```
IA quiere: rm -rf /importante
        ↓
Sistema: "⚠️ Acción de alto riesgo. ¿Confirmar?"
        ↓
Usuario decide
```


---

## 🔀 Flujo Real de Procesamiento de Peticiones

### La IA NO "entiende" tu petición mágicamente

Sigue este proceso:

```
┌─────────────────────────────────────────────────────────┐
│  TÚ ESCRIBES: "hazme un login con react y node"        │
│  (con errores, desordenado, incompleto)                │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  1. SYSTEM PROMPT (instrucciones fijas)                │
│     - "Eres OpenHands agent"                           │
│     - "Primero EXPLORA, luego ANALIZA, luego IMPLEMENTA"│
│     - "No asumas, verifica"                            │
│     - "Usa herramientas, no imagines"                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  2. TOOLS DISPONIBLES (la IA solo puede hacer esto)    │
│     - terminal (bash)                                  │
│     - file_editor (crear/editar archivos)              │
│     - browser (navegar web)                            │
│     - task_tracker (lista de tareas)                   │
│     - think (razonar sin actuar)                       │
│     - finish (terminar)                                │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  3. LLM RECIBE TODO JUNTO:                             │
│     [System Prompt] + [Tools] + [Tu mensaje] + [Historial] │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  4. LLM DECIDE:                                        │
│     → Llamar tool (ejecutar algo)                      │
│     → Responder texto (preguntar/aclarar)              │
│     → Finish (terminar)                                │
└─────────────────────────────────────────────────────────┘
                    ↓                    ↓
          Si llama tool:          Si responde texto:
          → Se ejecuta REAL       → Te muestra
          → Resultado vuelve      → Espera tu input
          → LLM ve resultado
          → Decide siguiente
                    ↓
            (LOOP hasta finish)
```

---

## 🔧 Manejo de Peticiones Desordenadas

### El System Prompt le dice:

```
1. EXPLORATION: Primero EXPLORA y ENTIENDE antes de actuar
2. ANALYSIS: Considera múltiples opciones
3. TESTING: Crea tests para verificar
4. IMPLEMENTATION: Haz cambios mínimos y enfocados
5. VERIFICATION: Verifica que funcione
```

### Ejemplo con Petición Desordenada

**Tú:** "oye necesito que el botón este rojo y también que se conecte a la base de datos pero primero instala node y ah también un login"

**La IA Internamente:**

```
1. Lee el system prompt → "Primero EXPLORA"
2. Usa terminal → ls -la (ve qué hay)
3. Usa file_editor → revisa archivos existentes
4. Usa think → "El usuario quiere: login + botón rojo + DB + instalar node"
5. Usa task_tracker → Crea lista ordenada:
   ☐ Instalar Node
   ☐ Crear login
   ☐ Conectar DB
   ☐ Estilizar botón
```

**Luego ejecuta en orden.**

### La Clave

| Lo que parece | Lo que realmente pasa |
|---------------|----------------------|
| "La IA entiende" | El LLM infiere basado en contexto |
| "La IA sigue un flujo" | El System Prompt le ORDENA seguir pasos |
| "La IA no se va por las ramas" | Las Tools LIMITAN lo que puede hacer |
| "La IA verifica" | Ejecuta comando → VE output real |

**La IA no "imagina" resultados. Los VE.**

- Crea archivo → lo lee para confirmar
- Ejecuta código → ve el output real
- Abre página → ve si cargó o dio error

**Eso la obliga a mantenerse en la realidad.**


---

## 📊 Comparación de Modelos LLM

### Modelos Gratis que se Aproximan a Claude

| Modelo | Cómo usarlo gratis | Nivel vs Claude |
|--------|-------------------|-----------------|
| **DeepSeek V3** | API muy barata (~$0.14/1M tokens) | 85-90% |
| **Llama 3.1 70B** | Groq (free tier) o Ollama (local) | ~75-80% |
| **Qwen 2.5 72B** | Ollama (local) | ~75-80% |
| **Gemini 2.0 Flash** | Google AI Studio (free tier) | 70-75% |

### Mi Recomendación

**DeepSeek V3** - Es lo más cercano a Claude en calidad y el más barato que existe. No es gratis pero cuesta casi nada.

### Modelos Open Source para Runpod

Si quieres instalarlo en Runpod:

| Modelo | VRAM necesaria | Nivel vs Claude |
|--------|----------------|-----------------|
| Llama 3.1 70B | ~40GB (A100) | ~75-80% |
| Qwen 2.5 72B | ~40GB (A100) | ~75-80% |
| DeepSeek Coder V2 236B | ~120GB (2-3x A100) | ~85% |
| Llama 3.1 405B | ~200GB+ (4x A100) | ~85% |

**Lo más práctico en Runpod:** Llama 3.1 70B o Qwen 2.5 72B con una A100 40GB (~$1.5-2/hora)

### Comparación Directa

| Aspecto | Llama 3.1 70B | Llama 3.1 405B | DeepSeek V3 API |
|---------|---------------|----------------|-----------------|
| Calidad | 75-80% | ~90% | 85-90% |
| Costo/hora | ~$1.5/hr (A100) | ~$6-8/hr (4x A100) | ~$0.14/1M tokens |
| Setup | Complejo | Muy complejo | Ninguno |
| Mantenimiento | Tú | Tú | Ellos |
| Disponibilidad | Mientras pagues GPU | Mientras pagues GPU | 24/7 |

### Mi Recomendación Final

**→ DeepSeek V3 API**

Por qué:
1. **Más barato** - Pagas solo lo que usas, no por hora
2. **Mejor calidad** que Llama 70B
3. **Cero setup** - Funciona en 5 minutos
4. **Sin mantener servidores**

Cuándo elegir Runpod:
- Si necesitas **privacidad total** (datos sensibles)
- Si vas a usar **24/7 sin parar** (ahí puede salir más barato)

---

## 🛠️ Componentes para Replicar el Sistema

Si quieres construir algo similar a OpenHands, necesitas:

### 1. System Prompt
Instrucciones rígidas de comportamiento para el LLM.

### 2. Tools (Funciones Limitadas)
Definir qué puede llamar el LLM:
- Terminal (bash)
- File Editor
- Browser
- Task Tracker

### 3. Loop de Ejecución
```
while not finished:
    response = llm.generate(context)
    if response.is_tool_call:
        result = execute_tool(response.tool)
        context.add(result)
    else:
        show_to_user(response.text)
```

### 4. Historial
Mantener contexto de la conversación.

### 5. Ejecución Real
Conectar a terminal, archivos, browser reales.

---

## 📚 Recursos Adicionales

- **Documentación Oficial**: https://docs.openhands.dev/
- **GitHub**: https://github.com/All-Hands-AI/OpenHands
- **SDK**: https://docs.openhands.dev/sdk/
- **CLI**: https://docs.openhands.dev/openhands/usage/run-openhands/cli-mode
- **GUI Local**: https://docs.openhands.dev/openhands/usage/run-openhands/local-setup

---

## ✅ Resumen Ejecutivo

| Concepto | Resumen |
|----------|---------|
| **¿Qué es OpenHands?** | Framework/orquestador para agentes de IA, agnóstico al modelo |
| **¿Qué LLM usa?** | El que tú configures (Claude, GPT, Llama, etc.) via LiteLLM |
| **¿Cómo controla a la IA?** | System Prompt + Tools limitados + Loop de verificación |
| **¿Por qué no inventa cosas?** | Porque VE resultados reales, no imagina |
| **¿Modelo gratis recomendado?** | DeepSeek V3 API (casi gratis) o Llama 3.1 70B local |

---

*Documento generado con información de la documentación oficial de OpenHands y análisis del funcionamiento interno del sistema.*

