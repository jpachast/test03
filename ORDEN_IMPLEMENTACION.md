# 📋 ORDEN DE IMPLEMENTACIÓN

## 🗂️ ¿Qué es cada cosa?

```
test03/
│
├── 📚 DOCUMENTACIÓN (NO SE EJECUTA, solo referencia)
│   ├── OpenHands_Doc_Oficial.md      → Documentación completa de OpenHands
│   ├── PLAN_CHAT_OPENHANDS_VERIFICADO.md → Plan y código verificado
│   ├── ARQUITECTURA_PROYECTO.md      → Arquitectura del chat
│   └── ORDEN_IMPLEMENTACION.md       → Este archivo
│
├── 📜 PROMPTS DE REFERENCIA (El SDK ya los tiene internamente)
│   └── prompts/
│       ├── system_prompt.j2          → Prompt principal (REFERENCIA)
│       ├── security_policy.j2        → Políticas de seguridad
│       ├── google_gemini.j2          → Ajustes para Gemini
│       └── ...                       → Otros prompts
│
├── 🗑️ ARCHIVOS DE EJEMPLO (Se pueden eliminar)
│   ├── index.html
│   ├── estilos.css
│   └── ejemplo.txt
│
└── 🚀 PROYECTO REAL (HAY QUE CREAR)
    └── openhands-chat/               → El chat funcional
        ├── app.py
        ├── config/
        ├── core/
        └── ...
```

---

## 🔗 ¿Cómo se relacionan?

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  📚 DOCUMENTACIÓN          📜 PROMPTS              🚀 PROYECTO  │
│  ─────────────────         ─────────              ───────────── │
│                                                                 │
│  OpenHands_Doc_Oficial.md                                       │
│         │                                                       │
│         │ (explica cómo funciona)                               │
│         ▼                                                       │
│  PLAN_VERIFICADO.md ──────► Los prompts .j2 son                 │
│         │                   REFERENCIA de lo que                │
│         │                   el SDK usa internamente             │
│         │                          │                            │
│         │                          │                            │
│         ▼                          ▼                            │
│  ARQUITECTURA.md ──────────► openhands-chat/                    │
│                              (proyecto real)                    │
│                                    │                            │
│                                    ▼                            │
│                              El SDK carga                       │
│                              automáticamente                    │
│                              los prompts .j2                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📍 ORDEN DE IMPLEMENTACIÓN

### Paso 1: Limpiar archivos de ejemplo

```bash
# Eliminar archivos que no necesitamos
rm index.html estilos.css ejemplo.txt
```

### Paso 2: Crear estructura del proyecto

```bash
# Crear directorio del proyecto real
mkdir -p openhands-chat/{config,core,ui}
```

### Paso 3: Crear archivos de configuración

```
openhands-chat/
├── .env                  # Variables de entorno
├── .env.example          # Ejemplo para compartir
├── requirements.txt      # Dependencias
└── config/
    ├── __init__.py
    ├── settings.py       # Configuración
    └── rules.py          # Reglas del agente
```

### Paso 4: Crear núcleo del chat

```
openhands-chat/
└── core/
    ├── __init__.py
    ├── agent.py          # Configuración del agente + tools
    ├── conversation.py   # Loop del chat
    └── workspace.py      # Manejo de proyectos/git
```

### Paso 5: Crear punto de entrada

```
openhands-chat/
└── app.py                # Menú principal
```

### Paso 6: (Opcional) Interfaz web

```
openhands-chat/
└── ui/
    ├── __init__.py
    └── web.py            # FastAPI para interfaz web
```

---

## 🗺️ ESTRUCTURA FINAL

```
test03/
│
├── 📚 Documentación
│   ├── OpenHands_Doc_Oficial.md
│   ├── PLAN_CHAT_OPENHANDS_VERIFICADO.md
│   ├── ARQUITECTURA_PROYECTO.md
│   └── ORDEN_IMPLEMENTACION.md
│
├── 📜 Prompts (referencia)
│   └── prompts/
│       └── *.j2
│
└── 🚀 openhands-chat/           ← PROYECTO FUNCIONAL
    ├── app.py                   ← EJECUTAR ESTE
    ├── requirements.txt
    ├── .env
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py
    │   └── rules.py
    ├── core/
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── conversation.py
    │   └── workspace.py
    └── projects/                ← Aquí se crean los proyectos
        ├── mi-crm/
        ├── mi-api/
        └── ...
```

---

## ▶️ CÓMO EJECUTAR

```bash
# 1. Entrar al proyecto
cd openhands-chat

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar API key
export LLM_API_KEY="tu-api-key-de-gemini"

# 4. Ejecutar
python app.py
```

---

## 📊 RESUMEN

| Archivo/Carpeta | Tipo | ¿Se ejecuta? | Propósito |
|-----------------|------|--------------|-----------|
| `OpenHands_Doc_Oficial.md` | Documentación | ❌ | Referencia |
| `PLAN_VERIFICADO.md` | Documentación | ❌ | Plan y código |
| `ARQUITECTURA.md` | Documentación | ❌ | Diseño del proyecto |
| `prompts/*.j2` | Referencia | ❌ | Ver cómo son los prompts |
| `openhands-chat/` | **Proyecto** | ✅ | **El chat funcional** |
| `openhands-chat/app.py` | Código | ✅ | **Punto de entrada** |

---

## ❓ ¿LOS PROMPTS .J2 SE USAN?

**NO directamente.** El SDK de OpenHands ya los tiene internamente.

Los descargamos como **REFERENCIA** para:
1. Ver cómo funciona el system prompt
2. Entender las reglas de seguridad
3. Ver los ajustes por modelo (Gemini, Claude, etc.)

Pero cuando haces:
```python
from openhands.sdk import Agent
agent = Agent(llm=llm, tools=tools)
```

El SDK automáticamente carga sus propios prompts .j2 internos.

---

## ✅ SIGUIENTE PASO

¿Quieres que cree el proyecto `openhands-chat/` con todos los archivos funcionales?
