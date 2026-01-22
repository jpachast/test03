# OpenHands Chat - Estado de Features

## Servidor Hetzner
- **IP:** 178.156.193.106
- **SSH:** root / kCJHc3sVMwNv
- **Container:** openhands-chat
- **Puerto:** 80 → 12000
- **URL:** http://178.156.193.106/chat/29

## Estado de Features (Verificado 2026-01-22)

| # | Feature | Backend | Frontend | Verificado Visual | Estado |
|---|---------|---------|----------|-------------------|--------|
| 1 | MCP Protocol | ✅ /api/mcp/* | ✅ | ✅ | **100%** |
| 2 | Code Embeddings | ✅ /api/semantic/* | ✅ | ✅ | **100%** |
| 3 | Codemaps | ✅ /api/codemap/* | ✅ | ✅ | **100%** |
| 4 | Checkpoints | ✅ /api/checkpoints/* | ✅ | ✅ | **100%** |
| 5 | Voice Input | ❌ Sin router | ✅ JS existe | ❌ | **PENDIENTE** |
| 6 | Background Agents | ✅ /api/background/* | ✅ | ✅ | **100%** |
| 7 | Auto-Fix Loop | ✅ /api/autofix/* | ✅ | ✅ | **100%** |
| 8 | Web Scraper | ✅ /api/scraper/* | ✅ | ✅ | **100%** |
| 9 | Test Generator | ✅ /api/tests/* | ✅ | ✅ | **100%** |
| 10 | Multi-Agent | ✅ /api/advanced/* | ✅ | ✅ | **100%** |
| 11 | Monte Carlo | ✅ /api/advanced/ml/* | ✅ | ✅ | **100%** |
| 12 | Diff Preview | ✅ /api/diff/* | ✅ | ✅ | **100%** |
| + | Code Parser | ✅ /api/codeparser/* | ✅ | ✅ | **100%** |

## PENDIENTE

### Voice Input (Punto 5)
- **Archivo existe:** `/app/core/voice_input.py`
- **JS existe:** `/app/static/js/voice_input.js`
- **Falta:** Crear `/app/ui/routers/voice_endpoints.py` y registrar en `web.py`

## Reglas para el Agente

1. **SIEMPRE verificar código en Hetzner antes de responder**
2. **NUNCA asumir** - conectar y revisar archivos reales
3. **Actualizar este archivo** cuando se complete una feature
4. **Probar visualmente** en http://178.156.193.106/chat/29 antes de confirmar

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
