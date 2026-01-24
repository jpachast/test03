# Función Fibonacci - Implementaciones que hemos discutido

# 1. Implementación recursiva simple (la que empezaste)
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

# 2. Implementación iterativa optimizada
def fibonacci_iterativo(n):
    if n <= 1:
        return n
    
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    return b

# 3. Implementación con memoización
def fibonacci_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memo(n-1, memo) + fibonacci_memo(n-2, memo)
    return memo[n]

# Probando fibonacci(10) como solicitaste
print("🧮 Resultados de fibonacci(10):")
print(f"Recursiva simple: {fibonacci(10)}")
print(f"Iterativa: {fibonacci_iterativo(10)}")
print(f"Con memoización: {fibonacci_memo(10)}")

# Secuencia completa hasta 10 para verificar
print("\n📊 Secuencia Fibonacci completa:")
for i in range(11):
    print(f"fibonacci({i}) = {fibonacci_iterativo(i)}")