# Configuración del Entorno de Trabajo

## URLs Públicas Disponibles

Este entorno tiene acceso a los siguientes puertos públicos:

| Puerto Local | URL Pública |
|--------------|-------------|
| 12000 | https://work-1-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev |
| 12001 | https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev |

## ⚠️ REGLAS CRÍTICAS para Despliegue

### OBLIGATORIO: Matar servidor anterior

**SIEMPRE** antes de levantar un servidor nuevo, DEBES matar el anterior:

```bash
# PASO 1: MATAR SERVIDOR ANTERIOR (OBLIGATORIO - SIEMPRE EJECUTAR)
pkill -f "http.server 12001" 2>/dev/null || true
sleep 1

# PASO 2: IR AL DIRECTORIO DEL PROYECTO ACTUAL
cd /workspace/project/test03/04_proyecto/openhands-chat/projects/NOMBRE_PROYECTO

# PASO 3: LEVANTAR SERVIDOR NUEVO
python3 -m http.server 12001 > server.log 2>&1 &
sleep 2
```

### Mostrar URL

**NUNCA** muestres `localhost:12001` - el usuario no puede acceder a localhost.
**SIEMPRE** muestra la URL pública:

```
🌐 Tu app está en: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev
```

### Ejemplo Correcto ✅:
```
✅ Tu app está en: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev
```

### Ejemplo INCORRECTO ❌:
```
❌ Tu app está en: http://localhost:12001
```

## ¿Por qué matar el servidor anterior?

Si no matas el servidor anterior, el puerto 12001 seguirá sirviendo el proyecto viejo y el usuario verá contenido incorrecto.
