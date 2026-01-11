# Configuración del Entorno de Trabajo

## URLs Públicas Disponibles

Este entorno tiene acceso a los siguientes puertos públicos:

| Puerto Local | URL Pública |
|--------------|-------------|
| 12000 | https://work-1-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev |
| 12001 | https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev |

## Reglas IMPORTANTES para Despliegue

1. **SIEMPRE** que levantes un servidor web, usa el puerto **12001**
2. **NUNCA** muestres `localhost:12001` al usuario
3. **SIEMPRE** muestra la URL pública correspondiente

### Ejemplo Correcto:
```
✅ Tu app está en: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev
```

### Ejemplo INCORRECTO (no hacer):
```
❌ Tu app está en: http://localhost:12001
```

## Comando para Levantar Servidor

Cuando necesites levantar un servidor HTTP simple:
```bash
cd /ruta/al/proyecto && python3 -m http.server 12001 > server.log 2>&1 &
```

Después de ejecutar el comando, **espera 2 segundos** y muestra:
```
🌐 Tu app está en: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev
```
