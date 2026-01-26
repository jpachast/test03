# OpenHands Chat - Estado de Features

## Servidor Hetzner
- **IP:** 178.156.193.106
- **SSH:** root / kCJHc3sVMwNv
- **Container:** openhands-chat
- **Puerto:** 80 → 12000
- **URL:** http://178.156.193.106/chat/29

## Estado de Features (Verificado 2026-01-24)

| # | Feature | Backend | Frontend | Verificado Visual | Estado |
|---|---------|---------|----------|-------------------|--------|
| 1 | MCP Protocol | ✅ /api/mcp/* + chat.py | ✅ | ✅ VERIFICADO | **100%** |
| 2 | Code Embeddings | ✅ /api/semantic/* | ✅ | ✅ | **100%** |
| 3 | Codemaps | ✅ /api/codemap/* | ✅ | ✅ | **100%** |
| 4 | Checkpoints | ✅ /api/checkpoints/* | ✅ | ✅ | **100%** |
| 5 | Voice Input | ✅ /api/voice/* | ✅ JS existe | ✅ | **100%** |
| 6 | Background Agents | ✅ /api/background/* | ✅ | ✅ | **100%** |
| 7 | Auto-Fix Loop | ✅ /api/autofix/* | ✅ | ✅ | **100%** |
| 8 | Web Scraper | ✅ /api/scraper/* | ✅ | ✅ | **100%** |
| 9 | Test Generator | ✅ /api/tests/* | ✅ | ✅ | **100%** |
| 10 | Multi-Agent | ✅ /api/advanced/* | ✅ | ✅ | **100%** |
| 11 | Monte Carlo | ✅ /api/advanced/ml/* | ✅ | ✅ | **100%** |
| 12 | Diff Preview | ✅ /api/diff/* | ✅ | ✅ | **100%** |
| + | Code Parser | ✅ /api/codeparser/* | ✅ | ✅ | **100%** |

## 🚀 Integración de Features en Conversaciones (COMPLETADO 2026-01-24)

### ⚡ FIX APLICADO (2026-01-24)
- **Bug encontrado**: `detectFeatures()` solo buscaba en `responseText`, no en `userMessage`
- **Fix aplicado**: Ahora combina features de ambos (`featuresFromResponse` + `featuresFromUser`)
- **Archivo**: `/app/static/js/features_chat_integration.js` líneas 720-722
- **Commit**: `b1cb1bc`

### ✅ INTEGRACIÓN COMPLETA AL 100%

El agente ahora **conoce y usa activamente** las features durante las conversaciones.

### 1. System Prompt del Agente (agent.py)
Agregada sección `<INTEGRATED_TOOLS>` (líneas 560-617) que instruye al agente:
- **AUTO-FIX**: Corregir errores automáticamente cuando hay Traceback
- **TEST GENERATOR**: Generar tests cuando el usuario lo pida
- **WEB SCRAPER**: Extraer contenido de URLs
- **DIFF PREVIEW**: Mostrar cambios git
- **SEMANTIC SEARCH**: Buscar funcionalidad en el código

### 2. Backend (Endpoints)
| Archivo | Ubicación | Función |
|---------|-----------|---------|
| autofix_chat_router.py | `/app/ui/routers/` | Endpoint `/api/chat/autofix/*` |
| chat_autofix_integration.py | `/app/core/` | Detección y corrección de errores |

### 3. Frontend (JavaScript)
| Archivo | Ubicación | Función |
|---------|-----------|---------|
| features_chat_integration.js | `/app/static/js/` | Integración multi-feature |
| autofix_chat.js | `/app/static/js/` | Helper de auto-fix |

### 4. Reglas de Uso Automático
El agente fue instruido con estas reglas:
1. **Si hay error en ejecución** → USA AUTO-FIX inmediatamente
2. **Si piden tests** → USA TEST GENERATOR
3. **Si mencionan URL + extraer** → USA WEB SCRAPER
4. **Si preguntan por cambios** → USA DIFF PREVIEW
5. **Si buscan funcionalidad** → USA SEMANTIC SEARCH

### Integración en index.js
```javascript
// Después de mostrar mensaje del agente (línea ~5456)
if (window.processResponseWithFeatures) {
    const lastMessage = document.querySelector('.message.assistant:last-child');
    setTimeout(() => processResponseWithFeatures(lastMessage, messageToShow, fullMessage), 500);
}
```

## ✅ MCP Protocol - Verificación Completa (2026-01-24)

### Prueba realizada via HTTP API:
```
1. Limpiar historial conversación 29 ✅
2. Enviar: "Mi nombre es MIGUEL y mi color favorito es MORADO" ✅
3. Agente respondió: "He guardado tu información: MIGUEL, MORADO" ✅
4. Enviar: "¿Cuál es mi nombre y mi color favorito?" ✅
5. Agente respondió: "Tu nombre es MIGUEL y tu color favorito es MORADO" ✅
```

### Integración MCP en chat.py:
- **Línea 808-818:** Obtiene contexto MCP para cada mensaje
- **Línea 894-897:** Agrega contexto al mensaje del usuario  
- **Línea 957-964:** Guarda respuestas del agente en MCP
- **15+ referencias** a MCP en el archivo

### Archivos clave:
- `/app/core/mcp_chat_backend.py` - Backend de integración
- `/app/core/mcp_protocol.py` - Protocolo MCP base
- `/app/ui/routers/chat.py` - Integración en flujo de chat

## COMPLETADO

### Voice Input (Punto 5) - ✅ IMPLEMENTADO
- **Backend:** `/app/core/voice_input.py`
- **Frontend:** `/app/static/js/voice_input.js`
- **Router:** `/app/ui/routers/voice_endpoints.py`
- **Endpoints:**
  - GET `/api/voice/status` - Estado de configuración
  - POST `/api/voice/transcribe` - Transcribir audio
  - POST `/api/voice/test` - Probar conexión
- **Backends soportados:**
  - Web Speech API (gratis, navegador)
  - Groq Whisper (gratis, tier gratuito)
  - OpenAI Whisper (de pago)

## Reglas para el Agente

1. **SIEMPRE verificar código en Hetzner antes de responder**
2. **NUNCA asumir** - conectar y revisar archivos reales
3. **Actualizar este archivo** cuando se complete una feature
4. **Probar visualmente** en http://178.156.193.106/chat/29 antes de confirmar

---

## 🚨 REGLAS OBLIGATORIAS DE DEBUGGING (Lección 2026-01-26)

### ⚠️ ANTES de tocar código de streaming/SSE - HACER ESTO PRIMERO:

```bash
# TEST DE TIMESTAMPS - OBLIGATORIO PRIMERO (30 segundos)
docker exec openhands-chat bash -c '
curl -sN http://localhost:12000/api/chat/test-basic 2>&1 | while read line; do
    echo "$(date +%H:%M:%S.%3N): $line"
done
'
```

**Interpretar resultados:**
- Timestamps **SEPARADOS** (~500ms) → Problema es RED/FRONTEND
- Timestamps **JUNTOS** (<50ms) → Problema es BACKEND ← buscar aquí

### 🔴 ANTIPATTERNS CONOCIDOS (NO HACER NUNCA):

| Código | Problema | Solución |
|--------|----------|----------|
| `async def generate_events()` + `threading.Thread` | BUFFERING | Usar `def` (sync) |
| `async def` + `queue.Queue()` | BUFFERING | Usar `def` (sync) |
| `await asyncio.sleep()` en generator con threads | No funciona | Usar `time.sleep()` |

### ✅ PATRÓN CORRECTO para streaming con threads:

```python
# CORRECTO - sync generator con threads
def generate_events():
    q = queue.Queue()
    thread = threading.Thread(target=run_agent, args=(q,))
    thread.start()
    
    while True:
        event = q.get(timeout=0.1)
        if event is None:
            break
        yield f"data: {json.dumps(event)}\n\n"
        time.sleep(0.01)  # sync sleep, NO await
```

### 📋 CHECKLIST cuando usuario reporta "eventos llegan juntos":

1. [ ] **NO asumir** que es frontend
2. [ ] **NO asumir** que es Docker/red  
3. [ ] **PRIMERO** hacer test de timestamps (comando arriba)
4. [ ] **VERIFICAR** si `generate_events()` es `async def` o `def`
5. [ ] **SI ES** `async def` con threads → CAMBIAR a `def`

### 🏗️ Arquitectura de chat.py (RECORDAR):

- `generate_events()` **DEBE SER** `def` (sync), **NO** `async def`
- Usa `threading.Thread` internamente para ejecutar el agente
- Usa `queue.Queue()` para comunicación thread → generator
- **Por eso DEBE ser sync** - async + threads = buffering

### 📅 Historial de bugs SSE:

| Fecha | Bug | Causa | Fix | Tiempo perdido |
|-------|-----|-------|-----|----------------|
| 2026-01-26 | Eventos llegan juntos | `async def` + threads | Cambiar a `def` | 2 días |

## Comandos útiles

```bash
# Conectar a Hetzner
ssh root@178.156.193.106  # password: kCJHc3sVMwNv

# Ver logs del container
docker logs openhands-chat --tail 50

# Ejecutar comando en container
docker exec openhands-chat <comando>

# Verificar endpoint
docker exec openhands-chat curl -s http://localhost:12000/api/<endpoint>
```
