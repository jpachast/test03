# Configuración del Entorno de Trabajo

## Sistema de URLs por Proyecto

El servidor de proyectos **YA ESTÁ CORRIENDO** en el puerto 12001.
Sirve TODOS los proyectos automáticamente como subdirectorios.

### URL Base
```
https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev/
```

### URLs de Proyectos
Cada proyecto tiene su propia URL basada en el nombre de la carpeta:

| Proyecto | URL |
|----------|-----|
| calculadora | https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev/calculadora/ |
| mi-app | https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev/mi-app/ |
| juego | https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev/juego/ |

## ⚠️ REGLAS para Despliegue

### NO necesitas levantar servidor
El servidor ya está corriendo. Solo crea los archivos y muestra la URL.

### Formato de URL
```
🌐 Tu app está en: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev/NOMBRE_PROYECTO/
```

### Ejemplo Correcto ✅:
```
✅ Tu app está en: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev/calculadora/
```

### Ejemplo INCORRECTO ❌:
```
❌ Tu app está en: http://localhost:12001
❌ Tu app está en: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev  (falta el nombre del proyecto)
```

## Ventajas de este sistema
- ✅ Todos los proyectos están disponibles simultáneamente
- ✅ No hay conflictos de puertos
- ✅ No necesitas matar/reiniciar servidores
- ✅ Cada proyecto tiene su URL permanente
