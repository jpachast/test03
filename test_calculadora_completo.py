import unittest
import pytest
from calculadora import suma, resta, multiplica, divide


class TestCalculadora(unittest.TestCase):
    """Tests completos para la calculadora"""

    def test_suma_positivos(self):
        """Test suma con números positivos"""
        self.assertEqual(suma(2, 3), 5)
        self.assertEqual(suma(10, 20), 30)
        self.assertEqual(suma(0, 5), 5)

    def test_suma_negativos(self):
        """Test suma con números negativos"""
        self.assertEqual(suma(-2, -3), -5)
        self.assertEqual(suma(-10, 5), -5)
        self.assertEqual(suma(10, -5), 5)

    def test_suma_decimales(self):
        """Test suma con números decimales"""
        self.assertAlmostEqual(suma(2.5, 3.7), 6.2)
        self.assertAlmostEqual(suma(-1.5, 2.5), 1.0)

    def test_suma_cero(self):
        """Test suma con cero"""
        self.assertEqual(suma(0, 0), 0)
        self.assertEqual(suma(5, 0), 5)
        self.assertEqual(suma(0, -5), -5)

    def test_resta_positivos(self):
        """Test resta con números positivos"""
        self.assertEqual(resta(5, 3), 2)
        self.assertEqual(resta(10, 10), 0)
        self.assertEqual(resta(20, 5), 15)

    def test_resta_negativos(self):
        """Test resta con números negativos"""
        self.assertEqual(resta(-5, -3), -2)
        self.assertEqual(resta(-10, 5), -15)
        self.assertEqual(resta(10, -5), 15)

    def test_resta_decimales(self):
        """Test resta con números decimales"""
        self.assertAlmostEqual(resta(5.5, 2.3), 3.2)
        self.assertAlmostEqual(resta(-1.5, 2.5), -4.0)

    def test_resta_cero(self):
        """Test resta con cero"""
        self.assertEqual(resta(0, 0), 0)
        self.assertEqual(resta(5, 0), 5)
        self.assertEqual(resta(0, 5), -5)

    def test_multiplica_positivos(self):
        """Test multiplicación con números positivos"""
        self.assertEqual(multiplica(2, 3), 6)
        self.assertEqual(multiplica(5, 4), 20)
        self.assertEqual(multiplica(1, 10), 10)

    def test_multiplica_negativos(self):
        """Test multiplicación con números negativos"""
        self.assertEqual(multiplica(-2, 3), -6)
        self.assertEqual(multiplica(-5, -4), 20)
        self.assertEqual(multiplica(5, -2), -10)

    def test_multiplica_decimales(self):
        """Test multiplicación con números decimales"""
        self.assertAlmostEqual(multiplica(2.5, 4), 10.0)
        self.assertAlmostEqual(multiplica(-1.5, 2), -3.0)

    def test_multiplica_cero(self):
        """Test multiplicación con cero"""
        self.assertEqual(multiplica(0, 5), 0)
        self.assertEqual(multiplica(5, 0), 0)
        self.assertEqual(multiplica(0, 0), 0)

    def test_divide_positivos(self):
        """Test división con números positivos"""
        self.assertEqual(divide(6, 2), 3)
        self.assertEqual(divide(20, 4), 5)
        self.assertEqual(divide(10, 1), 10)

    def test_divide_negativos(self):
        """Test división con números negativos"""
        self.assertEqual(divide(-6, 2), -3)
        self.assertEqual(divide(-20, -4), 5)
        self.assertEqual(divide(20, -4), -5)

    def test_divide_decimales(self):
        """Test división con números decimales"""
        self.assertAlmostEqual(divide(7.5, 2.5), 3.0)
        self.assertAlmostEqual(divide(-9, 3), -3.0)

    def test_divide_por_cero(self):
        """Test división por cero - debe lanzar excepción"""
        with self.assertRaises(ValueError):
            divide(5, 0)
        with self.assertRaises(ValueError):
            divide(-5, 0)
        with self.assertRaises(ValueError):
            divide(0, 0)

    def test_operaciones_grandes(self):
        """Test con números grandes"""
        self.assertEqual(suma(1000000, 2000000), 3000000)
        self.assertEqual(resta(1000000, 500000), 500000)
        self.assertEqual(multiplica(1000, 1000), 1000000)
        self.assertEqual(divide(1000000, 1000), 1000)


# Tests con pytest (estilo funcional)
def test_suma_basica():
    assert suma(2, 3) == 5

def test_resta_basica():
    assert resta(5, 3) == 2

def test_multiplica_basica():
    assert multiplica(3, 4) == 12

def test_divide_basica():
    assert divide(8, 2) == 4

def test_divide_por_cero_pytest():
    with pytest.raises(ValueError):
        divide(10, 0)


if __name__ == '__main__':
    unittest.main()