#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)

def factorial(n):
    """Calcula el factorial de n de forma recursiva"""
    if n <= 1:
        return 1
    return n * factorial(n-1)

def factorial_iterativo(n):
    """Versión iterativa del factorial (más eficiente)"""
    if n <= 1:
        return 1
    
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado

def mostrar_factorial_paso_a_paso(n):
    """Muestra el cálculo del factorial paso a paso"""
    print(f"{Fore.CYAN}🔢 Calculando {n}! paso a paso:{Style.RESET_ALL}")
    
    if n <= 1:
        print(f"{Fore.GREEN}   {n}! = 1{Style.RESET_ALL}")
        return 1
    
    # Mostrar la expansión
    expansion = []
    for i in range(n, 0, -1):
        expansion.append(str(i))
    
    print(f"{Fore.YELLOW}   {n}! = {' × '.join(expansion)}{Style.RESET_ALL}")
    
    # Calcular paso a paso
    resultado = 1
    pasos = []
    for i in range(1, n + 1):
        resultado *= i
        pasos.append(f"{i}! = {resultado}")
    
    for paso in pasos:
        print(f"{Fore.WHITE}   {paso}{Style.RESET_ALL}")
    
    return resultado

def main():
    print(f"{Fore.MAGENTA}{'='*50}")
    print(f"🎯 DEMOSTRACIÓN DE FUNCIÓN FACTORIAL")
    print(f"{'='*50}{Style.RESET_ALL}")
    
    # Probar varios números
    numeros = [0, 1, 3, 5, 7, 10]
    
    for n in numeros:
        print(f"\n{Fore.BLUE}📊 Probando factorial({n}):{Style.RESET_ALL}")
        
        # Versión recursiva
        fact_rec = factorial(n)
        print(f"{Fore.GREEN}   Recursivo: {n}! = {fact_rec:,}{Style.RESET_ALL}")
        
        # Versión iterativa
        fact_iter = factorial_iterativo(n)
        print(f"{Fore.CYAN}   Iterativo: {n}! = {fact_iter:,}{Style.RESET_ALL}")
        
        # Verificar que ambos dan el mismo resultado
        if fact_rec == fact_iter:
            print(f"{Fore.WHITE}   ✅ Ambos métodos coinciden{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}   ❌ ERROR: Los métodos no coinciden{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}🔍 Ejemplo detallado para 5!:{Style.RESET_ALL}")
    mostrar_factorial_paso_a_paso(5)
    
    print(f"\n{Fore.MAGENTA}📈 Comparación de crecimiento:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'n':>3} | {'n!':>15} | {'Crecimiento':>12}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*3}+{'-'*15}+{'-'*12}{Style.RESET_ALL}")
    
    anterior = 1
    for i in range(1, 11):
        fact = factorial(i)
        if i == 1:
            crecimiento = "---"
        else:
            crecimiento = f"{fact/anterior:.1f}x"
        print(f"{Fore.CYAN}{i:>3} | {fact:>15,} | {crecimiento:>11}{Style.RESET_ALL}")
        anterior = fact

if __name__ == "__main__":
    main()