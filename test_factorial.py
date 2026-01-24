import unittest

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

class TestFactorial(unittest.TestCase):
    
    def test_factorial_casos_base(self):
        """Prueba casos base: 0 y 1"""
        self.assertEqual(factorial(0), 1)
        self.assertEqual(factorial(1), 1)
    
    def test_factorial_numeros_pequenos(self):
        """Prueba números pequeños conocidos"""
        self.assertEqual(factorial(2), 2)
        self.assertEqual(factorial(3), 6)
        self.assertEqual(factorial(4), 24)
        self.assertEqual(factorial(5), 120)
    
    def test_factorial_numeros_medios(self):
        """Prueba números medios"""
        self.assertEqual(factorial(6), 720)
        self.assertEqual(factorial(7), 5040)
        self.assertEqual(factorial(10), 3628800)
    
    def test_factorial_negativos(self):
        """Prueba números negativos (deberían retornar 1 según la implementación)"""
        self.assertEqual(factorial(-1), 1)
        self.assertEqual(factorial(-5), 1)
        self.assertEqual(factorial(-10), 1)
    
    def test_factorial_tipo_datos(self):
        """Verifica que el resultado sea entero"""
        resultado = factorial(5)
        self.assertIsInstance(resultado, int)
        self.assertEqual(type(resultado), int)

if __name__ == '__main__':
    unittest.main()