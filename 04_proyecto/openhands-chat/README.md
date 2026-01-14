# 🤖 OpenHands Chat

Chat de desarrollo con IA basado en OpenHands SDK.
Interfaz web para conversaciones con agentes que pueden ejecutar código, navegar la web y crear proyectos.

## ✨ Características

- ✅ **Crear proyectos** desde cero o clonar repos Git
- ✅ **Integración GitHub** - 9 repos visibles, pull/push desde la UI
- ✅ **Navegador integrado** - Screenshots automáticos cuando el agente navega
- ✅ **Code-server** - VS Code en el navegador por conversación
- ✅ **Prompts de OpenHands** - System prompt completo sin reducir
- ✅ **LLMSummarizingCondenser** - Manejo de contextos largos como OpenHands
- ✅ **API key encriptada** - Cifrado Fernet con soporte legacy
- ✅ **Token GitHub persistente** - Se guarda encriptado en BD

## 🚀 Instalación Rápida

```bash
# Clonar el repo
git clone https://github.com/jpachast/test03.git
cd test03/04_proyecto/openhands-chat

# Ejecutar script de instalación (instala todo automáticamente)
chmod +x start.sh
./start.sh
```

El script `start.sh` hace todo automáticamente:
1. Instala dependencias de Python (`requirements.txt`)
2. Instala navegador Playwright (para screenshots)
3. Instala code-server (VS Code en navegador)
4. Inicia el servidor en puerto 12000

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

### Browser CLI
El agente puede navegar la web usando comandos bash:
```bash
python -m core.browser navigate "https://www.google.com"
python -m core.browser state      # Ver elementos interactivos
python -m core.browser click "button.submit"
python -m core.browser type "input#search" "texto"
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
