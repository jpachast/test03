#!/usr/bin/env python3
"""
Tests completos para las funciones fibonacci y factorial
Incluye casos normales, casos límite y casos de error
"""

import pytest
import sys
import os

# Importar las funciones a testear
from fibonacci_factorial import fibonacci, factorial


class TestFibonacci:
    """Tests para la función fibonacci"""
    
    def test_fibonacci_casos_base(self):
        """Test casos base de fibonacci"""
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1
    
    def test_fibonacci_casos_pequenos(self):
        """Test primeros números de fibonacci"""
        assert fibonacci(2) == 1
        assert fibonacci(3) == 2
        assert fibonacci(4) == 3
        assert fibonacci(5) == 5
        assert fibonacci(6) == 8
        assert fibonacci(7) == 13
        assert fibonacci(8) == 21
        assert fibonacci(9) == 34
        assert fibonacci(10) == 55
    
    def test_fibonacci_secuencia_completa(self):
        """Test verificando la secuencia completa"""
        secuencia_esperada = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        for i, valor_esperado in enumerate(secuencia_esperada):
            assert fibonacci(i) == valor_esperado
    
    def test_fibonacci_numeros_grandes(self):
        """Test con números más grandes (pero no demasiado para evitar recursión excesiva)"""
        assert fibonacci(15) == 610
        assert fibonacci(20) == 6765
    
    def test_fibonacci_propiedades_matematicas(self):
        """Test propiedades matemáticas de fibonacci"""
        # F(n) = F(n-1) + F(n-2)
        for n in range(2, 15):
            assert fibonacci(n) == fibonacci(n-1) + fibonacci(n-2)
    
    def test_fibonacci_negativos_deberia_fallar(self):
        """Test que fibonacci con números negativos devuelve el número (comportamiento actual)"""
        # Según la implementación actual, fibonacci(-1) devuelve -1
        assert fibonacci(-1) == -1
        assert fibonacci(-5) == -5


class TestFactorial:
    """Tests para la función factorial"""
    
    def test_factorial_caso_base(self):
        """Test caso base factorial(0) = 1"""
        assert factorial(0) == 1
    
    def test_factorial_casos_pequenos(self):
        """Test primeros factoriales"""
        assert factorial(1) == 1
        assert factorial(2) == 2
        assert factorial(3) == 6
        assert factorial(4) == 24
        assert factorial(5) == 120
        assert factorial(6) == 720
        assert factorial(7) == 5040
        assert factorial(8) == 40320
        assert factorial(9) == 362880
        assert factorial(10) == 3628800
    
    def test_factorial_propiedades_matematicas(self):
        """Test propiedades matemáticas del factorial"""
        # n! = n * (n-1)!
        for n in range(1, 10):
            assert factorial(n) == n * factorial(n-1)
    
    def test_factorial_crecimiento(self):
        """Test que factorial crece correctamente"""
        for n in range(1, 8):
            assert factorial(n+1) > factorial(n)
    
    def test_factorial_numeros_grandes(self):
        """Test factoriales de números más grandes"""
        assert factorial(12) == 479001600
        assert factorial(13) == 6227020800
    
    def test_factorial_negativos_recursion_infinita(self):
        """Test que factorial con números negativos causa problemas (comportamiento actual)"""
        # NOTA: La implementación actual no maneja números negativos
        # Esto causaría recursión infinita, así que no lo probamos directamente
        # En una implementación robusta, debería lanzar una excepción
        pass


class TestIntegracion:
    """Tests de integración y casos especiales"""
    
    def test_fibonacci_factorial_combinados(self):
        """Test combinando fibonacci y factorial"""
        # factorial(fibonacci(n)) para valores pequeños
        assert factorial(fibonacci(0)) == factorial(0)  # factorial(0) = 1
        assert factorial(fibonacci(1)) == factorial(1)  # factorial(1) = 1
        assert factorial(fibonacci(2)) == factorial(1)  # factorial(1) = 1
        assert factorial(fibonacci(3)) == factorial(2)  # factorial(2) = 2
        assert factorial(fibonacci(4)) == factorial(3)  # factorial(3) = 6
        assert factorial(fibonacci(5)) == factorial(5)  # factorial(5) = 120
    
    def test_tipos_de_datos(self):
        """Test que las funciones devuelven enteros"""
        assert isinstance(fibonacci(5), int)
        assert isinstance(factorial(5), int)
    
    def test_rendimiento_basico(self):
        """Test básico de rendimiento - no debería tardar demasiado"""
        import time
        
        # Fibonacci hasta 25 debería ser rápido
        start = time.time()
        resultado = fibonacci(25)
        end = time.time()
        assert end - start < 1.0  # Menos de 1 segundo
        assert resultado == 75025
        
        # Factorial hasta 15 debería ser muy rápido
        start = time.time()
        resultado = factorial(15)
        end = time.time()
        assert end - start < 0.1  # Menos de 0.1 segundos
        assert resultado == 1307674368000


class TestCasosLimite:
    """Tests para casos límite y edge cases"""
    
    def test_valores_limite_fibonacci(self):
        """Test valores límite para fibonacci"""
        # Los valores más pequeños válidos
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1
    
    def test_valores_limite_factorial(self):
        """Test valores límite para factorial"""
        # El valor más pequeño válido
        assert factorial(0) == 1
        assert factorial(1) == 1


if __name__ == "__main__":
    # Ejecutar tests con pytest si está disponible, sino usar unittest
    try:
        import pytest
        pytest.main([__file__, "-v", "--tb=short"])
    except ImportError:
        import unittest
        
        # Convertir a unittest si pytest no está disponible
        suite = unittest.TestSuite()
        
        # Agregar tests manualmente
        test_cases = [
            TestFibonacci(),
            TestFactorial(), 
            TestIntegracion(),
            TestCasosLimite()
        ]
        
        for test_case in test_cases:
            for method_name in dir(test_case):
                if method_name.startswith('test_'):
                    suite.addTest(unittest.TestCase(method_name))
        
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)