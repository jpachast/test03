def fibonacci(n):
    """
    Calcula el n-ésimo número de Fibonacci
    F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)
    """
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

def fibonacci_iterativo(n):
    """
    Versión iterativa más eficiente
    """
    if n <= 1:
        return n
    
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    return b

def fibonacci_memoizado(n, memo={}):
    """
    Versión con memoización para optimizar
    """
    if n in memo:
        return memo[n]
    
    if n <= 1:
        memo[n] = n
        return n
    
    memo[n] = fibonacci_memoizado(n - 1, memo) + fibonacci_memoizado(n - 2, memo)
    return memo[n]

# Ejemplos de uso
if __name__ == "__main__":
    print("🔢 SECUENCIA DE FIBONACCI")
    print("=" * 30)
    
    # Mostrar primeros 10 números
    for i in range(10):
        fib_recursivo = fibonacci(i)
        fib_iterativo = fibonacci_iterativo(i)
        fib_memo = fibonacci_memoizado(i)
        
        print(f"F({i}) = {fib_recursivo}")
    
    print("\n⚡ COMPARACIÓN DE RENDIMIENTO:")
    import time
    
    n = 35
    
    # Recursivo (lento)
    start = time.time()
    result_rec = fibonacci(n)
    time_rec = time.time() - start
    
    # Iterativo (rápido)
    start = time.time()
    result_iter = fibonacci_iterativo(n)
    time_iter = time.time() - start
    
    # Memoizado (muy rápido)
    start = time.time()
    result_memo = fibonacci_memoizado(n)
    time_memo = time.time() - start
    
    print(f"F({n}) = {result_rec}")
    print(f"Recursivo: {time_rec:.4f}s")
    print(f"Iterativo: {time_iter:.6f}s")
    print(f"Memoizado: {time_memo:.6f}s")