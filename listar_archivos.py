#!/usr/bin/env python3
"""
Script para listar todos los archivos del proyecto actual
Incluye filtros y opciones de visualización
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def format_size(size_bytes):
    """Convierte bytes a formato legible (KB, MB, GB)"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def should_ignore(path, ignore_patterns):
    """Verifica si un archivo/directorio debe ser ignorado"""
    path_str = str(path).lower()
    for pattern in ignore_patterns:
        if pattern in path_str:
            return True
    return False

def listar_archivos(directorio=".", mostrar_ocultos=False, mostrar_detalles=True, filtro_extension=None):
    """
    Lista todos los archivos del directorio especificado
    
    Args:
        directorio (str): Directorio a explorar (por defecto actual)
        mostrar_ocultos (bool): Si mostrar archivos/directorios ocultos
        mostrar_detalles (bool): Si mostrar tamaño y fecha de modificación
        filtro_extension (str): Filtrar por extensión específica (ej: '.py', '.html')
    """
    
    # Patrones a ignorar (directorios comunes que suelen ser muy grandes)
    ignore_patterns = [
        '__pycache__', 'node_modules', '.git', '.venv', 'venv',
        '.pytest_cache', '.mypy_cache', 'dist', 'build', '.egg-info'
    ]
    
    directorio_path = Path(directorio).resolve()
    
    print(f"📁 LISTADO DE ARCHIVOS EN: {directorio_path}")
    print("=" * 80)
    
    archivos_encontrados = []
    directorios_encontrados = []
    total_size = 0
    
    try:
        for root, dirs, files in os.walk(directorio_path):
            root_path = Path(root)
            
            # Filtrar directorios a ignorar
            dirs[:] = [d for d in dirs if not should_ignore(root_path / d, ignore_patterns)]
            
            # Si no mostrar ocultos, filtrar directorios que empiecen con punto
            if not mostrar_ocultos:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Procesar archivos
            for file in files:
                file_path = root_path / file
                
                # Si no mostrar ocultos, saltar archivos que empiecen con punto
                if not mostrar_ocultos and file.startswith('.'):
                    continue
                
                # Filtrar por extensión si se especifica
                if filtro_extension and not file.lower().endswith(filtro_extension.lower()):
                    continue
                
                try:
                    stat = file_path.stat()
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Calcular ruta relativa
                    try:
                        relative_path = file_path.relative_to(directorio_path)
                    except ValueError:
                        relative_path = file_path
                    
                    archivos_encontrados.append({
                        'path': relative_path,
                        'size': size,
                        'modified': modified,
                        'extension': file_path.suffix
                    })
                    
                    total_size += size
                    
                except (OSError, PermissionError):
                    # Ignorar archivos que no se pueden leer
                    continue
            
            # Contar directorios
            for dir_name in dirs:
                dir_path = root_path / dir_name
                try:
                    relative_path = dir_path.relative_to(directorio_path)
                except ValueError:
                    relative_path = dir_path
                
                directorios_encontrados.append(str(relative_path))
    
    except PermissionError as e:
        print(f"❌ Error de permisos: {e}")
        return
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return
    
    # Ordenar archivos por nombre
    archivos_encontrados.sort(key=lambda x: str(x['path']))
    directorios_encontrados.sort()
    
    # Mostrar estadísticas
    print(f"📊 ESTADÍSTICAS:")
    print(f"   • Directorios: {len(directorios_encontrados)}")
    print(f"   • Archivos: {len(archivos_encontrados)}")
    print(f"   • Tamaño total: {format_size(total_size)}")
    print()
    
    # Mostrar directorios
    if directorios_encontrados:
        print("📂 DIRECTORIOS:")
        for i, dir_path in enumerate(directorios_encontrados[:20]):  # Mostrar máximo 20
            print(f"   {i+1:3d}. 📁 {dir_path}")
        
        if len(directorios_encontrados) > 20:
            print(f"   ... y {len(directorios_encontrados) - 20} directorios más")
        print()
    
    # Mostrar archivos
    if archivos_encontrados:
        print("📄 ARCHIVOS:")
        for i, archivo in enumerate(archivos_encontrados):
            if mostrar_detalles:
                size_str = format_size(archivo['size']).rjust(8)
                date_str = archivo['modified'].strftime('%Y-%m-%d %H:%M')
                ext_str = archivo['extension'] or 'sin ext'
                print(f"   {i+1:3d}. {size_str} | {date_str} | {ext_str:8s} | {archivo['path']}")
            else:
                print(f"   {i+1:3d}. {archivo['path']}")
    
    # Mostrar resumen por extensiones
    if archivos_encontrados:
        print()
        print("📈 RESUMEN POR EXTENSIONES:")
        extension_count = {}
        extension_size = {}
        
        for archivo in archivos_encontrados:
            ext = archivo['extension'] or 'sin extensión'
            extension_count[ext] = extension_count.get(ext, 0) + 1
            extension_size[ext] = extension_size.get(ext, 0) + archivo['size']
        
        # Ordenar por cantidad
        for ext, count in sorted(extension_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            size_str = format_size(extension_size[ext])
            print(f"   • {ext:12s}: {count:3d} archivos ({size_str})")

def main():
    """Función principal con opciones de línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lista archivos del proyecto actual")
    parser.add_argument("directorio", nargs="?", default=".", 
                       help="Directorio a explorar (por defecto: directorio actual)")
    parser.add_argument("--ocultos", action="store_true", 
                       help="Mostrar archivos y directorios ocultos")
    parser.add_argument("--simple", action="store_true", 
                       help="Mostrar solo nombres de archivos (sin detalles)")
    parser.add_argument("--extension", "-e", type=str, 
                       help="Filtrar por extensión específica (ej: .py, .html)")
    
    args = parser.parse_args()
    
    listar_archivos(
        directorio=args.directorio,
        mostrar_ocultos=args.ocultos,
        mostrar_detalles=not args.simple,
        filtro_extension=args.extension
    )

if __name__ == "__main__":
    main()