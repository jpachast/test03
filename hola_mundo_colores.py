#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplos de "Hola Mundo" con colores en Python
"""

# Método 1: Usando códigos ANSI escape
def hola_mundo_ansi():
    print("\n🎨 MÉTODO 1: Códigos ANSI Escape")
    print("\033[31m¡Hola Mundo en ROJO!\033[0m")
    print("\033[32m¡Hola Mundo en VERDE!\033[0m")
    print("\033[34m¡Hola Mundo en AZUL!\033[0m")
    print("\033[33m¡Hola Mundo en AMARILLO!\033[0m")
    print("\033[35m¡Hola Mundo en MAGENTA!\033[0m")
    print("\033[36m¡Hola Mundo en CIAN!\033[0m")

# Método 2: Usando colorama (instalación opcional)
def hola_mundo_colorama():
    try:
        from colorama import Fore, Back, Style, init
        init(autoreset=True)
        
        print("\n🌈 MÉTODO 2: Usando Colorama")
        print(Fore.RED + "¡Hola Mundo en ROJO!")
        print(Fore.GREEN + "¡Hola Mundo en VERDE!")
        print(Fore.BLUE + "¡Hola Mundo en AZUL!")
        print(Fore.YELLOW + "¡Hola Mundo en AMARILLO!")
        print(Fore.MAGENTA + "¡Hola Mundo en MAGENTA!")
        print(Fore.CYAN + "¡Hola Mundo en CIAN!")
        
        # Con fondo de color
        print(Back.RED + Fore.WHITE + "¡Hola con fondo ROJO!")
        print(Back.GREEN + Fore.BLACK + "¡Hola con fondo VERDE!")
        
    except ImportError:
        print("\n⚠️  Colorama no está instalado. Usa: pip install colorama")

# Método 3: Función personalizada con colores
def color_print(texto, color="blanco"):
    """Función para imprimir texto con colores"""
    colores = {
        "rojo": "\033[31m",
        "verde": "\033[32m",
        "amarillo": "\033[33m",
        "azul": "\033[34m",
        "magenta": "\033[35m",
        "cian": "\033[36m",
        "blanco": "\033[37m",
        "reset": "\033[0m"
    }
    
    color_code = colores.get(color.lower(), colores["blanco"])
    print(f"{color_code}{texto}{colores['reset']}")

def hola_mundo_personalizado():
    print("\n✨ MÉTODO 3: Función Personalizada")
    
    colores = ["rojo", "verde", "amarillo", "azul", "magenta", "cian"]
    
    for color in colores:
        color_print(f"¡Hola Mundo en {color.upper()}!", color)

# Método 4: Hola mundo con emojis y colores
def hola_mundo_emojis():
    print("\n🎉 MÉTODO 4: Con Emojis y Colores")
    
    mensajes = [
        ("\033[31m❤️  ¡Hola Mundo!\033[0m", "rojo"),
        ("\033[32m💚 ¡Hola Mundo!\033[0m", "verde"),
        ("\033[34m💙 ¡Hola Mundo!\033[0m", "azul"),
        ("\033[33m💛 ¡Hola Mundo!\033[0m", "amarillo"),
        ("\033[35m💜 ¡Hola Mundo!\033[0m", "magenta"),
        ("\033[36m🩵 ¡Hola Mundo!\033[0m", "cian")
    ]
    
    for mensaje, _ in mensajes:
        print(mensaje)

# Función principal
def main():
    print("🐍 PYTHON - HOLA MUNDO CON COLORES 🌈")
    print("=" * 50)
    
    # Ejecutar todos los métodos
    hola_mundo_ansi()
    hola_mundo_colorama()
    hola_mundo_personalizado()
    hola_mundo_emojis()
    
    print("\n🎨 ¡Todos los métodos ejecutados!")
    print("💡 Tip: Para usar colorama, instala con: pip install colorama")

if __name__ == "__main__":
    main()