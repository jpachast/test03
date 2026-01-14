# 🚨 INSTRUCCIONES CRÍTICAS PARA ESTE REPOSITORIO 🚨

## ⛔ NUNCA HACER:

### 0. CONFIGURACIÓN CORRECTA DE TOOLS (CRÍTICO!)
- Las tools se importan de `openhands.tools` y se usan con `Tool(name=X.name)`
- **CORRECTO**: `Tool(name=TerminalTool.name)` → nombre es "terminal"
- **CORRECTO**: `Tool(name=FileEditorTool.name)` → nombre es "file_editor"
- **INCORRECTO**: `Tool(name="TerminalTool")` → causa KeyError!
- Siempre usar `X.name`, NUNCA el nombre de la clase como string
- El agente se crea en: `core/agent.py` → `_create_agent_safe()`


### 1. NO TOCAR EL TOKEN DE GITHUB
- **NUNCA** sobrescribir el token de GitHub en la base de datos
- **NUNCA** usar `$GITHUB_TOKEN` del entorno para reemplazar el token guardado
- El token PAT del usuario (`ghp_...`) está correctamente configurado en `data/config.db`
- Si hay error 401 en GitHub, el problema es la ENCRIPTACIÓN, no el token

### 2. NO CAMBIAR LA ENCRIPTACIÓN
- La encriptación en `config/database.py` usa una clave FIJA
- **NUNCA** modificar `_get_cipher()` para usar variables de entorno
- Si el token no se desencripta, revisar que la clave sea la fija

## ✅ SIEMPRE HACER:

### Al iniciar la aplicación:
```bash
cd /workspace/project/test03/04_proyecto/openhands-chat
export PORT=12000
python app.py > server.log 2>&1 &
```

### URL de la aplicación:
- Puerto: 12000
- Verificar con: `curl http://localhost:12000/health`

### Si hay problemas con GitHub repos:
1. **PRIMERO** verificar que el token se desencripta bien:
```python
from config.database import Database
db = Database()
token = db.get_github_token()
print(token[:10])  # Debe mostrar "ghp_..." NO "gAAAAAB..."
```

2. Si muestra "gAAAAAB...", el problema es la encriptación, NO el token
3. **PEDIR AL USUARIO** que ingrese su token PAT en Settings → Integraciones

## 📁 Estructura del proyecto:
- App principal: `04_proyecto/openhands-chat/`
- Base de datos: `04_proyecto/openhands-chat/data/config.db`
- Configuración: `04_proyecto/openhands-chat/config/`

## 🔑 Token del usuario:
- Usuario: jpachast
- El token PAT está guardado en la BD (NO en este archivo por seguridad)
- Repos: 9 repositorios disponibles
- **NUNCA** reemplazar con $GITHUB_TOKEN del entorno (ese solo tiene 4 repos)
