# 📑 ÍNDICE DEL PROYECTO - BASE DE CONOCIMIENTO

## 🗂️ Estructura Organizada

```
test03/
│
├── 📑 INDICE.md                              ← ESTÁS AQUÍ
│
├── 📚 01_documentacion/                      ← PASO 1: Entender
│   └── OpenHands_Doc_Oficial.md              → Qué es, características, costos
│
├── 📋 02_plan/                               ← PASO 2: Planificar
│   ├── PLAN_CHAT_OPENHANDS_VERIFICADO.md     → Código verificado con SDK
│   ├── ARQUITECTURA_PROYECTO.md              → Diseño del proyecto
│   └── ORDEN_IMPLEMENTACION.md               → Pasos a seguir
│
├── 📜 03_prompts_referencia/                 ← PASO 3: Conocer prompts
│   ├── core/                                 → Prompts principales
│   │   ├── system_prompt.j2                  → Prompt base del agente
│   │   ├── security_policy.j2                → Políticas de seguridad
│   │   ├── security_risk_assessment.j2       → Evaluación de riesgos
│   │   ├── self_documentation.j2             → Auto-documentación
│   │   ├── system_prompt_interactive.j2      → Modo interactivo
│   │   ├── system_prompt_long_horizon.j2     → Tareas largas
│   │   ├── system_prompt_planning.j2         → Modo planificación
│   │   ├── system_prompt_tech_philosophy.j2  → Filosofía técnica
│   │   ├── in_context_learning_example.j2    → Ejemplos de aprendizaje
│   │   └── in_context_learning_example_suffix.j2
│   │
│   └── model_specific/                       → Ajustes por modelo
│       ├── google_gemini.j2                  → Para Gemini
│       ├── anthropic_claude.j2               → Para Claude
│       └── openai_gpt/
│           ├── gpt-5.j2                      → Para GPT-5
│           └── gpt-5-codex.j2                → Para GPT-5 Codex
│
└── 🚀 04_proyecto/                           ← PASO 4: Crear (pendiente)
    └── openhands-chat/                       → El proyecto funcional
```

---

## 📖 ORDEN DE LECTURA

| Paso | Carpeta | Archivo | Propósito |
|------|---------|---------|-----------|
| 1️⃣ | `01_documentacion/` | `OpenHands_Doc_Oficial.md` | Entender qué es OpenHands |
| 2️⃣ | `02_plan/` | `PLAN_CHAT_OPENHANDS_VERIFICADO.md` | Ver código verificado |
| 3️⃣ | `02_plan/` | `ARQUITECTURA_PROYECTO.md` | Entender el diseño |
| 4️⃣ | `02_plan/` | `ORDEN_IMPLEMENTACION.md` | Ver pasos a seguir |
| 5️⃣ | `03_prompts_referencia/` | `core/system_prompt.j2` | Ver prompt principal |
| 6️⃣ | `03_prompts_referencia/` | `model_specific/google_gemini.j2` | Ver ajustes Gemini |
| 7️⃣ | `04_proyecto/` | `openhands-chat/` | **CREAR EL PROYECTO** |

---

## 🔗 FLUJO DE CONOCIMIENTO

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  PASO 1: ENTENDER                                               │
│  01_documentacion/OpenHands_Doc_Oficial.md                      │
│  → Qué es OpenHands                                             │
│  → Modelo recomendado (Gemini 2.5 Pro)                          │
│  → Costos ($50-150 por proyecto grande)                         │
│                         │                                       │
│                         ▼                                       │
│  PASO 2: PLANIFICAR                                             │
│  02_plan/PLAN_CHAT_OPENHANDS_VERIFICADO.md                      │
│  → Código verificado con SDK oficial                            │
│  → Imports correctos                                            │
│  → Reglas de comportamiento                                     │
│                         │                                       │
│  02_plan/ARQUITECTURA_PROYECTO.md                               │
│  → Estructura de carpetas                                       │
│  → Archivos a crear                                             │
│  → Flujo de uso                                                 │
│                         │                                       │
│  02_plan/ORDEN_IMPLEMENTACION.md                                │
│  → Pasos numerados                                              │
│  → Qué crear primero                                            │
│                         │                                       │
│                         ▼                                       │
│  PASO 3: CONOCER PROMPTS (referencia)                           │
│  03_prompts_referencia/core/                                    │
│  → system_prompt.j2 (el principal)                              │
│  → security_policy.j2 (seguridad)                               │
│  → Otros prompts especializados                                 │
│                                                                 │
│  03_prompts_referencia/model_specific/                          │
│  → google_gemini.j2 (el que usaremos)                           │
│  → anthropic_claude.j2                                          │
│  → openai_gpt/                                                  │
│                         │                                       │
│                         ▼                                       │
│  PASO 4: CREAR PROYECTO                                         │
│  04_proyecto/openhands-chat/                                    │
│  → app.py                                                       │
│  → config/                                                      │
│  → core/                                                        │
│  → ¡FUNCIONAL!                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ RESUMEN EJECUTIVO

| Concepto | Valor |
|----------|-------|
| **Modelo** | Gemini 2.5 Pro |
| **Costo** | $1.25/1M input, $10/1M output |
| **Proyecto grande** | $50-150 total |
| **Tools incluidas** | terminal, file_editor, browser_use, task_tracker, glob, grep |

**El chat podrá:**
- ✅ Responder consultas
- ✅ Crear proyectos desde cero
- ✅ Clonar repos Git y hacer mejoras
- ✅ Instalar dependencias automáticamente
- ✅ Desplegar y mostrar link
- ✅ Ver en navegador (pruebas visuales)
- ✅ No tocar código que funciona

---

## 🚀 SIGUIENTE PASO

El proyecto funcional se creará en:
```
04_proyecto/openhands-chat/
```

**¿Listo para crear el proyecto?**
