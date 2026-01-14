# 🤖 OpenHands Chat

Chat de desarrollo con IA basado en OpenHands SDK.
Interfaz web para conversaciones con agentes que pueden ejecutar código, navegar la web y crear proyectos.

## ✨ Características

- ✅ **Crear proyectos** desde cero o clonar repos Git
- ✅ **Integración GitHub** - Pull/push desde la UI
- ✅ **Navegación web** - El agente puede ver páginas web (curl/httpx)
- ✅ **Code-server** - VS Code en el navegador por conversación
- ✅ **Terminal de solo lectura** - Muestra comandos del agente en tiempo real
- ✅ **Task Tracker** - Lista de tareas visual como OpenHands
- ✅ **Markdown completo** - Tablas, código, listas renderizadas
- ✅ **Prompts de OpenHands** - System prompt completo del SDK
- ✅ **LLMSummarizingCondenser** - Manejo de contextos largos
- ✅ **API key encriptada** - Cifrado Fernet
- ✅ **100% Auto-instalación** - Solo ejecuta `python app.py`

## 🚀 Instalación Rápida

```bash
# Clonar el repo
git clone https://github.com/jpachast/test03.git
cd test03/04_proyecto/openhands-chat

# ¡Solo esto! La app auto-instala todo
python app.py
```

**¡Eso es todo!** La app auto-instala:
1. ✅ Dependencias Python (requirements.txt)
2. ✅ Code-server (VS Code en navegador)
3. ✅ Inicia el servidor en puerto 12000

**No necesitas** ejecutar pip install, ./start.sh, ni nada más.

## ⚙️ Configuración

1. Abre http://localhost:12000/settings (o tu URL de producción)
2. Configura tu **API Key de Gemini** (Google AI Studio)
3. Configura tu **Token de GitHub** (para repos privados)
4. ¡Listo!

### Obtener API Key de Gemini
1. Ve a https://aistudio.google.com/apikey
2. Crea una nueva API key
3. Copia y pega en Settings

### Obtener Token de GitHub
1. Ve a https://github.com/settings/tokens
2. Genera un nuevo token (classic) con permisos `repo`
3. Copia y pega en Settings

## 📁 Estructura del Proyecto

```
openhands-chat/
├── app.py                  # Punto de entrada principal
├── start.sh                # Script de instalación automática
├── requirements.txt        # Dependencias Python
├── config/
│   ├── database.py         # SQLite + encriptación (dual-cipher)
│   ├── settings.py         # Configuración general
│   └── rules.py            # Prompts completos de OpenHands
├── core/
│   ├── agent.py            # Agente con LLMSummarizingCondenser
│   ├── browser.py          # CLI para navegación web + screenshots
│   ├── workspace.py        # Manejo de proyectos
│   ├── github_service.py   # Integración GitHub API
│   ├── code_server.py      # VS Code por conversación
│   └── app_server.py       # Servidor de apps dinámico
├── ui/
│   ├── web.py              # FastAPI routes principales
│   ├── routers/
│   │   ├── chat.py         # API de chat + detección screenshots
│   │   ├── browser.py      # API de screenshots
│   │   └── settings.py     # API de configuración
│   └── templates/          # HTML (Jinja2)
├── static/
│   ├── css/                # Estilos
│   └── js/                 # JavaScript frontend
├── data/
│   └── config.db           # Base de datos SQLite (API keys encriptadas)
└── projects/               # Proyectos clonados/creados
```

## 🔧 Componentes Clave

### LLMSummarizingCondenser
OpenHands usa condensers para manejar contextos largos sin reducir prompts:
```python
condenser = LLMSummarizingCondenser(
    llm=llm,           # Usa el mismo LLM para resumir
    max_size=240,      # Máximo eventos antes de condensar
    keep_first=2,      # Mantener primeros N eventos
)
```

### Navegación Web
El agente usa curl para ver páginas web (más estable que Playwright):
```bash
# El agente ejecuta automáticamente:
curl -sL "https://example.com" | head -200
```

### Dual-Cipher Encryption
Soporte para tokens antiguos y nuevos:
- v1 (legacy): salt dinámico + password de instalación
- v2 (actual): salt fijo + password fijo

## 💰 Costos de API (Gemini)

| Modelo | Input (1M tokens) | Output (1M tokens) |
|--------|-------------------|---------------------|
| Gemini 2.5 Pro | $1.25 | $10.00 |
| Gemini 2.5 Flash | $0.30 | $2.50 |
| Gemini 2.0 Flash | $0.10 | $0.40 |

## 🔐 Seguridad

- API keys encriptadas con Fernet (cryptography)
- Base de datos local SQLite
- Tokens nunca se envían a terceros
- Soporte para migración de tokens legacy

## 🐛 Troubleshooting

### El agente dice "Tarea completada" sin hacer nada
- Verifica que tu API key esté configurada correctamente
- Revisa `/health` para ver el estado

### No aparecen los screenshots
- Haz clic en el botón 🌐 (Navegador) en el panel derecho
- Los screenshots se guardan en memoria por conversación

### Error de contexto excedido
- El LLMSummarizingCondenser debería manejarlo automáticamente
- Si persiste, inicia una nueva conversación

## 📝 Licencia

MIT

## 🔗 Referencias

- [OpenHands SDK Docs](https://docs.openhands.dev/sdk)
- [Context Condenser Guide](https://docs.openhands.dev/sdk/guides/context-condenser)
- [Google AI Studio](https://aistudio.google.com/)
