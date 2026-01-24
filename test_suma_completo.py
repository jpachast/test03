#!/usr/bin/env python3
"""
Tests completos para la función suma
Generado automáticamente siguiendo el patrón exitoso de factorial
"""

import unittest
import pytest
from calculadora import suma


class TestSumaBasicos(unittest.TestCase):
    """Tests básicos para la función suma"""
    
    def test_suma_numeros_positivos(self):
        """Test suma con números enteros positivos"""
        self.assertEqual(suma(2, 3), 5)
        self.assertEqual(suma(10, 15), 25)
        self.assertEqual(suma(100, 200), 300)
        self.assertEqual(suma(1, 1), 2)
    
    def test_suma_numeros_negativos(self):
        """Test suma con números negativos"""
        self.assertEqual(suma(-2, -3), -5)
        self.assertEqual(suma(-10, -15), -25)
        self.assertEqual(suma(-1, -1), -2)
    
    def test_suma_positivo_negativo(self):
        """Test suma entre números positivos y negativos"""
        self.assertEqual(suma(5, -3), 2)
        self.assertEqual(suma(-5, 3), -2)
        self.assertEqual(suma(10, -10), 0)
        self.assertEqual(suma(-7, 12), 5)
    
    def test_suma_con_cero(self):
        """Test suma con cero (elemento neutro)"""
        self.assertEqual(suma(0, 0), 0)
        self.assertEqual(suma(5, 0), 5)
        self.assertEqual(suma(0, 5), 5)
        self.assertEqual(suma(-3, 0), -3)
        self.assertEqual(suma(0, -3), -3)
    
    def test_suma_numeros_decimales(self):
        """Test suma con números decimales"""
        self.assertAlmostEqual(suma(2.5, 3.7), 6.2, places=7)
        self.assertAlmostEqual(suma(0.1, 0.2), 0.3, places=7)
        self.assertAlmostEqual(suma(-1.5, 2.8), 1.3, places=7)
        self.assertAlmostEqual(suma(3.14, 2.86), 6.0, places=7)
    
    def test_suma_numeros_grandes(self):
        """Test suma con números grandes"""
        self.assertEqual(suma(1000000, 2000000), 3000000)
        self.assertEqual(suma(999999999, 1), 1000000000)
        self.assertEqual(suma(-1000000, 500000), -500000)


class TestSumaAvanzados(unittest.TestCase):
    """Tests avanzados para la función suma"""
    
    def test_suma_tipos_mixtos(self):
        """Test suma entre enteros y flotantes"""
        self.assertEqual(suma(5, 2.0), 7.0)
        self.assertEqual(suma(3.0, 4), 7.0)
        self.assertAlmostEqual(suma(2.5, 3), 5.5, places=7)
    
    def test_suma_precision_flotante(self):
        """Test precisión con números flotantes"""
        resultado = suma(0.1, 0.1)
        self.assertAlmostEqual(resultado, 0.2, places=10)
        
        resultado = suma(0.123456789, 0.987654321)
        self.assertAlmostEqual(resultado, 1.11111111, places=8)
    
    def test_suma_tipo_resultado(self):
        """Test que verifica el tipo del resultado"""
        # Entero + Entero = Entero
        resultado = suma(3, 4)
        self.assertIsInstance(resultado, int)
        
        # Float + Entero = Float
        resultado = suma(3.0, 4)
        self.assertIsInstance(resultado, float)
        
        # Entero + Float = Float
        resultado = suma(3, 4.0)
        self.assertIsInstance(resultado, float)


# Tests con pytest (más modernos)
class TestSumaPytest:
    """Tests con pytest para mayor flexibilidad"""
    
    @pytest.mark.parametrize("a, b, esperado", [
        # Casos básicos
        (1, 2, 3),
        (0, 0, 0),
        (5, -5, 0),
        (-3, -7, -10),
        
        # Casos con decimales
        (2.5, 1.5, 4.0),
        (0.1, 0.9, 1.0),
        (-1.2, 2.7, 1.5),
        
        # Casos extremos
        (1000000, 1000000, 2000000),
        (-999, 999, 0),
        (0.0001, 0.0002, 0.0003),
    ])
    def test_suma_casos_parametrizados(self, a, b, esperado):
        """Test parametrizado con múltiples casos"""
        if isinstance(esperado, float):
            assert abs(suma(a, b) - esperado) < 1e-10
        else:
            assert suma(a, b) == esperado
    
    def test_suma_propiedades_matematicas(self):
        """Test propiedades matemáticas de la suma"""
        # Propiedad conmutativa: a + b = b + a
        assert suma(3, 5) == suma(5, 3)
        assert suma(-2, 7) == suma(7, -2)
        assert suma(1.5, 2.8) == suma(2.8, 1.5)
        
        # Elemento neutro: a + 0 = a
        assert suma(42, 0) == 42
        assert suma(0, -15) == -15
        assert suma(3.14, 0) == 3.14
    
    def test_suma_casos_especiales(self):
        """Test casos especiales y límites"""
        # Números muy pequeños
        assert abs(suma(1e-10, 2e-10) - 3e-10) < 1e-15
        
        # Números muy grandes
        assert suma(1e10, 2e10) == 3e10
        
        # Suma que resulta en cero
        assert suma(123, -123) == 0
        assert suma(-456.789, 456.789) == 0


def test_suma_rendimiento():
    """Test de rendimiento básico"""
    import time
    
    inicio = time.time()
    
    # Ejecutar muchas sumas
    for i in range(10000):
        suma(i, i + 1)
    
    fin = time.time()
    duracion = fin - inicio
    
    # Debe completarse en menos de 1 segundo
    assert duracion < 1.0, f"La función suma es muy lenta: {duracion:.4f}s"


if __name__ == "__main__":
    print("🧪 Ejecutando tests completos para la función suma...")
    print("=" * 60)
    
    # Ejecutar tests con unittest
    print("\n📋 EJECUTANDO TESTS BÁSICOS (unittest):")
    unittest.main(verbosity=2, exit=False)
    
    # Ejecutar tests con pytest (si está disponible)
    try:
        print("\n🚀 EJECUTANDO TESTS AVANZADOS (pytest):")
        pytest.main([__file__, "-v", "--tb=short"])
    except ImportError:
        print("⚠️  pytest no disponible, solo se ejecutaron tests básicos")