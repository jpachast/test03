# 🔧 FIX: Streaming SSE en Tiempo Real

## Fecha: 2026-01-26

## Problema
Los eventos SSE (Server-Sent Events) llegaban todos juntos al final en lugar de en tiempo real. Los indicadores de progreso no cambiaban dinámicamente.

## Causa Raíz
El generador `generate_events()` en `chat.py` era una función `async def` que usaba threads internamente con `queue.Queue()`. 

**Mezclar async generators con threads causa buffering** porque el event loop de asyncio no procesa los yields correctamente cuando hay un thread bloqueando.

## Solución

### Cambio 1: Convertir async generator a sync generator

**Antes (MAL):**
```python
async def generate_events():
    yield f"data: ..."
    # ... código con threads ...
    await asyncio.sleep(0.02)
```

**Después (BIEN):**
```python
def generate_events():
    yield f"data: ..."
    # ... código con threads ...
    time.sleep(0.01)
```

### Cambio 2: Reemplazar await asyncio.sleep por time.sleep

En `ui/routers/chat.py`, buscar y reemplazar:
- `async def generate_events():` → `def generate_events():`
- `await asyncio.sleep` → `time.sleep`

### Archivos Adicionales Creados

#### `/static/js/terminal_fix.js`
```javascript
(function(){
    window.addTerminalCommand=function(c){
        if(window.xterm)window.xterm.writeln("$ "+c)
    };
    window.addTerminalOutput=function(o,e){
        if(window.xterm&&o)o.split("\n").forEach(function(l){
            if(l.trim())window.xterm.writeln(l)
        })
    }
})();
```

#### `/static/js/minimal_sse.js`
Script que maneja el streaming SSE con timestamps para debugging.

### Agregar scripts a index.html

Antes de `</body>`:
```html
<script src="/static/js/terminal_fix.js"></script>
<script src="/static/js/minimal_sse.js?v=3"></script>
```

## Verificación

### Test de streaming (dentro del container):
```bash
curl -sN http://localhost:12000/api/chat/test-basic | while read line; do
    echo "$(date +%H:%M:%S.%3N): $line"
done
```

**Resultado esperado:** Cada evento debe llegar separado por ~500ms

```
20:36:56.900: data: {"step": 1}
20:36:57.400: data: {"step": 2}  ← +500ms
20:36:57.901: data: {"step": 3}  ← +501ms
```

## Nota sobre Docker Port Proxy

El Docker port proxy (80 → 12000) puede agregar buffering adicional. Si persiste el problema:
1. Usar `--network host` en Docker
2. O configurar nginx con `proxy_buffering off`

## Comandos para aplicar el fix

```bash
# Dentro del container
docker exec openhands-chat python3 -c "
with open('/app/ui/routers/chat.py', 'r') as f:
    c = f.read()
c = c.replace('async def generate_events():', 'def generate_events():')
c = c.replace('await asyncio.sleep', 'time.sleep')
with open('/app/ui/routers/chat.py', 'w') as f:
    f.write(c)
print('Fixed')
"

# Reiniciar container
docker restart openhands-chat
```

## Resumen

| Aspecto | Antes | Después |
|---------|-------|---------|
| Generador | `async def` | `def` (sync) |
| Sleep | `await asyncio.sleep()` | `time.sleep()` |
| Eventos | Llegan todos juntos | Llegan en tiempo real |
| Terminal | No mostraba output | Muestra comandos y output |
