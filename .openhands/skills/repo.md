# MEMORIA PERSISTENTE - OpenHands Chat (jpachast/test03)

## COMANDO PARA LEVANTAR LA WEB

**SIEMPRE que el usuario pida "levanta la web" o similar, ejecutar:**
```bash
cd /workspace/project/test03/04_proyecto/openhands-chat && python app.py > server.log 2>&1 &
```

Luego verificar:
```bash
sleep 5 && curl -s http://localhost:12000/health
```

## AUTO-INSTALACION GARANTIZADA

El archivo `app.py` tiene AUTO-INSTALACION integrada:
1. Detecta si faltan dependencias pip -> las instala automaticamente
2. Detecta si falta code-server -> lo instala automaticamente
3. Se reinicia automaticamente para cargar los modulos
4. NO necesitas ejecutar pip install manualmente
5. NO necesitas variables de entorno (PORT, HOST, etc.)
6. TODO esta HARDCODEADO en config/settings.py

## PUERTOS FIJOS (hardcodeados en config/settings.py)

- Puerto 12000: App principal (work-1)
- Puerto 12001: Servidor de proyectos (work-2)

## URLs

- App principal: https://work-1-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev
- Proyectos: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev

## ESTRUCTURA DEL PROYECTO

```
/workspace/project/test03/
├── .openhands/skills/repo.md  # Este archivo (memoria persistente)
└── 04_proyecto/openhands-chat/
    ├── app.py              # Punto de entrada (AUTO-INSTALA dependencias)
    ├── requirements.txt    # Dependencias pip
    ├── config/
    │   ├── settings.py     # Puertos HARDCODEADOS aqui
    │   ├── database.py     # Base de datos SQLite
    │   └── rules.py        # Prompts del agente
    ├── core/
    │   ├── agent.py        # Configuracion del agente
    │   └── code_server.py  # Integracion VS Code
    ├── ui/
    │   ├── web.py          # Rutas FastAPI
    │   └── templates/      # HTML
    ├── data/
    │   └── config.db       # Base de datos
    └── projects/           # Proyectos clonados
```

## LOGICA DEL PROYECTO

1. test03 = Proyecto principal = NO clonar, carpeta vacia
2. Otros repos (demo01, etc.) = Clonar en projects/{owner}-{repo}/chat{XX}/

## DEPENDENCIAS (en requirements.txt)

- openhands-sdk (NO openhands-tools, no existe)
- uvicorn, fastapi, jinja2
- httpx, aiohttp, websockets
- cryptography, gitpython, pydantic

## PROBLEMAS CONOCIDOS Y SOLUCIONES

### Servidor no inicia / Module not found
Solucion: Solo ejecuta `python app.py` - se auto-instala todo

### code-server no esta instalado
Solucion: Solo ejecuta `python app.py` - se auto-instala

### Paquetes se perdieron por reinicio del entorno
Solucion: Solo ejecuta `python app.py` - detecta y reinstala automaticamente
