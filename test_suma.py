import unittest
import pytest
from calculadora import suma


class TestSuma(unittest.TestCase):
    """Tests para la función suma usando unittest"""
    
    def test_suma_numeros_positivos(self):
        """Test suma de números positivos"""
        self.assertEqual(suma(2, 3), 5)
        self.assertEqual(suma(10, 15), 25)
        self.assertEqual(suma(100, 200), 300)
    
    def test_suma_numeros_negativos(self):
        """Test suma con números negativos"""
        self.assertEqual(suma(-2, -3), -5)
        self.assertEqual(suma(-10, 5), -5)
        self.assertEqual(suma(10, -5), 5)
    
    def test_suma_con_cero(self):
        """Test suma con cero"""
        self.assertEqual(suma(0, 0), 0)
        self.assertEqual(suma(5, 0), 5)
        self.assertEqual(suma(0, -3), -3)
    
    def test_suma_numeros_decimales(self):
        """Test suma con números decimales"""
        self.assertAlmostEqual(suma(2.5, 3.7), 6.2, places=1)
        self.assertAlmostEqual(suma(-1.5, 2.8), 1.3, places=1)
        self.assertAlmostEqual(suma(0.1, 0.2), 0.3, places=1)
    
    def test_suma_numeros_grandes(self):
        """Test suma con números grandes"""
        self.assertEqual(suma(1000000, 2000000), 3000000)
        self.assertEqual(suma(-9999999, 10000000), 1)
    
    def test_suma_tipos_mixtos(self):
        """Test suma con tipos mixtos (int y float)"""
        self.assertEqual(suma(5, 2.0), 7.0)
        self.assertEqual(suma(3.5, 4), 7.5)


# Tests con pytest (más modernos y concisos)
class TestSumaPytest:
    """Tests para la función suma usando pytest"""
    
    @pytest.mark.parametrize("a,b,esperado", [
        (1, 1, 2),
        (2, 3, 5),
        (0, 0, 0),
        (-1, 1, 0),
        (-5, -3, -8),
        (10, -10, 0),
        (100, 50, 150),
        (0.5, 0.5, 1.0),
        (2.7, 1.3, 4.0),
        (-2.5, 3.5, 1.0)
    ])
    def test_suma_casos_parametrizados(self, a, b, esperado):
        """Test parametrizado con múltiples casos"""
        resultado = suma(a, b)
        if isinstance(esperado, float):
            assert abs(resultado - esperado) < 0.1
        else:
            assert resultado == esperado
    
    def test_suma_propiedades_matematicas(self):
        """Test de propiedades matemáticas de la suma"""
        # Propiedad conmutativa: a + b = b + a
        assert suma(3, 5) == suma(5, 3)
        assert suma(-2, 7) == suma(7, -2)
        
        # Elemento neutro: a + 0 = a
        assert suma(42, 0) == 42
        assert suma(-15, 0) == -15
        
        # Inverso aditivo: a + (-a) = 0
        assert suma(8, -8) == 0
        assert suma(-12, 12) == 0
    
    def test_suma_casos_extremos(self):
        """Test casos extremos"""
        # Números muy grandes
        assert suma(999999999, 1) == 1000000000
        
        # Números muy pequeños
        assert suma(0.0001, 0.0002) == pytest.approx(0.0003, rel=1e-3)
        
        # Precisión flotante
        assert suma(0.1, 0.2) == pytest.approx(0.3, rel=1e-10)


if __name__ == '__main__':
    # Ejecutar tests de unittest
    unittest.main()