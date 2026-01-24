#!/usr/bin/env python3
"""
Ejemplos de código Python con diferentes características
Autor: OpenHands Assistant
Fecha: 2025
"""

import os
import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Proyecto:
    """Clase para representar un proyecto de software"""
    nombre: str
    version: str
    archivos: List[str]
    tamaño_mb: float
    
    def __post_init__(self):
        self.archivos_count = len(self.archivos)


class AnalizadorProyecto:
    """Analizador de estructura de proyectos"""
    
    def __init__(self, ruta_base: str):
        self.ruta_base = Path(ruta_base)
        self.extensiones_codigo = {'.py', '.js', '.html', '.css', '.json'}
    
    def listar_archivos(self) -> List[str]:
        """Lista todos los archivos del proyecto"""
        archivos = []
        
        try:
            for archivo in self.ruta_base.rglob('*'):
                if archivo.is_file() and not self._es_archivo_ignorado(archivo):
                    archivos.append(str(archivo.relative_to(self.ruta_base)))
        except Exception as e:
            print(f"❌ Error al listar archivos: {e}")
            return []
        
        return sorted(archivos)
    
    def _es_archivo_ignorado(self, archivo: Path) -> bool:
        """Verifica si un archivo debe ser ignorado"""
        ignorados = {
            '__pycache__', '.git', 'node_modules', 
            '.pytest_cache', '.venv', 'dist'
        }
        
        return any(parte in ignorados for parte in archivo.parts)
    
    def obtener_estadisticas(self) -> Dict[str, int]:
        """Obtiene estadísticas del proyecto"""
        archivos = self.listar_archivos()
        stats = {'total': len(archivos)}
        
        # Contar por extensión
        for archivo in archivos:
            ext = Path(archivo).suffix
            if ext in self.extensiones_codigo:
                stats[ext] = stats.get(ext, 0) + 1
        
        return stats
    
    async def analizar_async(self) -> Proyecto:
        """Análisis asíncrono del proyecto"""
        print("🔍 Analizando proyecto...")
        
        # Simular trabajo asíncrono
        await asyncio.sleep(0.1)
        
        archivos = self.listar_archivos()
        tamaño = self._calcular_tamaño_total()
        
        return Proyecto(
            nombre=self.ruta_base.name,
            version="1.0.0",
            archivos=archivos,
            tamaño_mb=tamaño
        )
    
    def _calcular_tamaño_total(self) -> float:
        """Calcula el tamaño total del proyecto en MB"""
        tamaño_bytes = 0
        
        for archivo in self.ruta_base.rglob('*'):
            if archivo.is_file():
                try:
                    tamaño_bytes += archivo.stat().st_size
                except OSError:
                    continue
        
        return round(tamaño_bytes / (1024 * 1024), 2)


def mostrar_resumen_bonito(proyecto: Proyecto):
    """Muestra un resumen visual del proyecto"""
    print("\n" + "="*50)
    print(f"📁 PROYECTO: {proyecto.nombre.upper()}")
    print("="*50)
    print(f"📊 Archivos totales: {proyecto.archivos_count}")
    print(f"💾 Tamaño: {proyecto.tamaño_mb} MB")
    print(f"🔖 Versión: {proyecto.version}")
    
    # Mostrar algunos archivos de ejemplo
    if proyecto.archivos:
        print("\n📄 Algunos archivos:")
        for i, archivo in enumerate(proyecto.archivos[:5]):
            emoji = "🐍" if archivo.endswith('.py') else "📄"
            print(f"   {emoji} {archivo}")
        
        if len(proyecto.archivos) > 5:
            print(f"   ... y {len(proyecto.archivos) - 5} archivos más")


async def main():
    """Función principal del programa"""
    try:
        # Configuración
        ruta_proyecto = "/workspace/project/test03"
        
        # Crear analizador
        analizador = AnalizadorProyecto(ruta_proyecto)
        
        # Análisis asíncrono
        proyecto = await analizador.analizar_async()
        
        # Mostrar resultados
        mostrar_resumen_bonito(proyecto)
        
        # Estadísticas adicionales
        stats = analizador.obtener_estadisticas()
        print(f"\n📈 ESTADÍSTICAS POR TIPO:")
        for ext, count in stats.items():
            if ext != 'total':
                print(f"   {ext}: {count} archivos")
        
        # Guardar resultado en JSON
        resultado = {
            'proyecto': proyecto.nombre,
            'archivos': proyecto.archivos_count,
            'tamaño_mb': proyecto.tamaño_mb,
            'estadisticas': stats
        }
        
        with open('analisis_proyecto.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Análisis guardado en 'analisis_proyecto.json'")
        
    except KeyboardInterrupt:
        print("\n⚠️  Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    finally:
        print("\n🏁 Análisis completado")


if __name__ == "__main__":
    # Ejecutar el programa principal
    asyncio.run(main())