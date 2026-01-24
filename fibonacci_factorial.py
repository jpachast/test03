def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

# Ejecutar las funciones como solicitaste
print(fibonacci(10))
print(factorial(5))