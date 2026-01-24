def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Ejemplos de uso
print("🔢 FUNCIÓN FIBONACCI")
print("=" * 30)

for i in range(10):
    resultado = fibonacci(i)
    print(f"fibonacci({i}) = {resultado}")

print("\n✨ Secuencia de Fibonacci:")
secuencia = [fibonacci(i) for i in range(10)]
print(secuencia)