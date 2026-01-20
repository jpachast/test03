def sumar_numeros(a, b):
    """
    Función que suma dos números y retorna el resultado.
    
    Args:
        a (int/float): Primer número
        b (int/float): Segundo número
    
    Returns:
        int/float: La suma de a y b
    """
    return a + b


# Ejemplo de uso
if __name__ == "__main__":
    # Pruebas de la función
    resultado1 = sumar_numeros(5, 3)
    resultado2 = sumar_numeros(10.5, 2.3)
    resultado3 = sumar_numeros(-4, 7)
    
    print(f"5 + 3 = {resultado1}")
    print(f"10.5 + 2.3 = {resultado2}")
    print(f"-4 + 7 = {resultado3}")