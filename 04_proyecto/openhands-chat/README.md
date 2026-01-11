# 🤖 OpenHands Chat

Chat de desarrollo con IA basado en OpenHands SDK.

## ✨ Características

- ✅ Crear proyectos desde cero
- ✅ Clonar repos Git existentes
- ✅ Instala dependencias automáticamente
- ✅ Despliega y muestra links
- ✅ Pruebas visuales en navegador
- ✅ No toca código que funciona
- ✅ API key encriptada en SQLite

## 🚀 Instalación

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar
python app.py

# 3. Abrir navegador
# http://localhost:8000
```

## ⚙️ Configuración

1. Abre http://localhost:8000/settings
2. Pega tu API key de Gemini
3. ¡Listo!

## 📁 Estructura

```
openhands-chat/
├── app.py              # Punto de entrada
├── config/
│   ├── database.py     # SQLite + encriptación
│   ├── settings.py     # Configuración
│   └── rules.py        # Reglas del agente
├── core/
│   ├── agent.py        # Agente OpenHands
│   └── workspace.py    # Manejo de proyectos
├── ui/
│   ├── web.py          # FastAPI server
│   └── templates/      # HTML
├── static/             # CSS
├── data/               # SQLite (se crea automático)
└── projects/           # Tus proyectos
```

## 💰 Costos

| Modelo | Input (1M) | Output (1M) |
|--------|------------|-------------|
| Gemini 2.5 Pro | $1.25 | $10.00 |
| Gemini 2.5 Flash | $0.30 | $2.50 |
| Gemini 2.0 Flash | $0.10 | $0.40 |

## 🔐 Seguridad

- API key encriptada con Fernet
- Base de datos local (SQLite)
- Nunca se envía la key a terceros

## 📝 Licencia

MIT
