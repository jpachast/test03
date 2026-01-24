import unittest
import pytest
from calculadora import suma, resta, multiplica, divide


class TestCalculadora(unittest.TestCase):
    """Tests para las funciones de calculadora básica"""
    
    def test_suma_numeros_positivos(self):
        """Test suma con números positivos"""
        self.assertEqual(suma(2, 3), 5)
        self.assertEqual(suma(10, 15), 25)
        self.assertEqual(suma(1, 1), 2)
    
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
        self.assertAlmostEqual(suma(2.5, 3.7), 6.2)
        self.assertAlmostEqual(suma(-1.5, 2.3), 0.8)
        self.assertAlmostEqual(suma(0.1, 0.2), 0.3)
    
    def test_suma_numeros_grandes(self):
        """Test suma con números grandes"""
        self.assertEqual(suma(1000000, 2000000), 3000000)
        self.assertEqual(suma(-999999, 1000000), 1)
    
    def test_resta_numeros_positivos(self):
        """Test resta con números positivos"""
        self.assertEqual(resta(5, 3), 2)
        self.assertEqual(resta(10, 4), 6)
        self.assertEqual(resta(7, 7), 0)
    
    def test_resta_numeros_negativos(self):
        """Test resta con números negativos"""
        self.assertEqual(resta(-5, -3), -2)
        self.assertEqual(resta(-10, 5), -15)
        self.assertEqual(resta(10, -5), 15)
    
    def test_resta_con_cero(self):
        """Test resta con cero"""
        self.assertEqual(resta(0, 0), 0)
        self.assertEqual(resta(5, 0), 5)
        self.assertEqual(resta(0, 3), -3)
    
    def test_resta_numeros_decimales(self):
        """Test resta con números decimales"""
        self.assertAlmostEqual(resta(5.7, 2.3), 3.4)
        self.assertAlmostEqual(resta(-1.5, -2.5), 1.0)
        self.assertAlmostEqual(resta(0.5, 0.2), 0.3)
    
    def test_resta_numeros_grandes(self):
        """Test resta con números grandes"""
        self.assertEqual(resta(3000000, 1000000), 2000000)
        self.assertEqual(resta(1000000, 2000000), -1000000)
    
    def test_multiplica_numeros_positivos(self):
        """Test multiplicación con números positivos"""
        self.assertEqual(multiplica(2, 3), 6)
        self.assertEqual(multiplica(5, 4), 20)
        self.assertEqual(multiplica(1, 10), 10)
    
    def test_multiplica_numeros_negativos(self):
        """Test multiplicación con números negativos"""
        self.assertEqual(multiplica(-2, 3), -6)
        self.assertEqual(multiplica(-5, -4), 20)
        self.assertEqual(multiplica(7, -2), -14)
    
    def test_multiplica_con_cero(self):
        """Test multiplicación con cero"""
        self.assertEqual(multiplica(0, 5), 0)
        self.assertEqual(multiplica(10, 0), 0)
        self.assertEqual(multiplica(0, 0), 0)
    
    def test_multiplica_numeros_decimales(self):
        """Test multiplicación con números decimales"""
        self.assertAlmostEqual(multiplica(2.5, 4), 10.0)
        self.assertAlmostEqual(multiplica(1.5, 2.5), 3.75)
        self.assertAlmostEqual(multiplica(-1.5, 2), -3.0)
    
    # TESTS PARA LA FUNCIÓN DIVIDE (CORREGIDA)
    def test_divide_numeros_positivos(self):
        """Test división con números positivos"""
        self.assertEqual(divide(10, 2), 5.0)
        self.assertEqual(divide(15, 3), 5.0)
        self.assertEqual(divide(8, 4), 2.0)
        self.assertEqual(divide(7, 2), 3.5)
    
    def test_divide_numeros_negativos(self):
        """Test división con números negativos"""
        self.assertEqual(divide(-10, 2), -5.0)
        self.assertEqual(divide(10, -2), -5.0)
        self.assertEqual(divide(-10, -2), 5.0)
        self.assertEqual(divide(-15, 3), -5.0)
    
    def test_divide_numeros_decimales(self):
        """Test división con números decimales"""
        self.assertAlmostEqual(divide(7.5, 2.5), 3.0)
        self.assertAlmostEqual(divide(10.0, 4.0), 2.5)
        self.assertAlmostEqual(divide(1.5, 0.5), 3.0)
        self.assertAlmostEqual(divide(-4.5, 1.5), -3.0)
    
    def test_divide_resultado_decimal(self):
        """Test división que resulta en decimal"""
        self.assertAlmostEqual(divide(1, 3), 0.3333333333333333)
        self.assertAlmostEqual(divide(2, 3), 0.6666666666666666)
        self.assertAlmostEqual(divide(5, 6), 0.8333333333333334)
    
    def test_divide_por_cero_lanza_error(self):
        """Test división por cero - debe lanzar ValueError"""
        with self.assertRaises(ValueError) as context:
            divide(10, 0)
        self.assertEqual(str(context.exception), "No se puede dividir por cero")
        
        with self.assertRaises(ValueError) as context:
            divide(-5, 0)
        self.assertEqual(str(context.exception), "No se puede dividir por cero")
        
        with self.assertRaises(ValueError) as context:
            divide(0, 0)
        self.assertEqual(str(context.exception), "No se puede dividir por cero")
    
    def test_divide_cero_entre_numero(self):
        """Test cero dividido entre cualquier número"""
        self.assertEqual(divide(0, 5), 0.0)
        self.assertEqual(divide(0, -3), 0.0)
        self.assertEqual(divide(0, 0.5), 0.0)
        self.assertEqual(divide(0, 100), 0.0)
    
    def test_divide_numeros_grandes(self):
        """Test división con números grandes"""
        self.assertEqual(divide(1000000, 1000), 1000.0)
        self.assertEqual(divide(2000000, 4000), 500.0)
        self.assertAlmostEqual(divide(999999, 333333), 3.0)


# Tests con pytest para casos adicionales
def test_suma_tipos_compatibles():
    """Test suma con tipos compatibles"""
    assert suma(True, False) == 1  # bool se convierte a int
    assert suma(2, 3.0) == 5.0  # int + float = float

def test_resta_tipos_compatibles():
    """Test resta con tipos compatibles"""
    assert resta(True, False) == 1  # bool se convierte a int
    assert resta(5.0, 2) == 3.0  # float - int = float

def test_multiplica_tipos_compatibles():
    """Test multiplicación con tipos compatibles"""
    assert multiplica(True, 2) == 2  # bool se convierte a int
    assert multiplica(2.5, 4) == 10.0  # float * int = float

def test_divide_tipos_compatibles():
    """Test división con tipos compatibles"""
    assert divide(True, 1) == 1.0  # bool se convierte a int
    assert divide(10.0, 2) == 5.0  # float / int = float

def test_divide_casos_especiales():
    """Test división casos especiales con pytest"""
    import pytest
    
    # Test división por cero con pytest
    with pytest.raises(ValueError, match="No se puede dividir por cero"):
        divide(1, 0)
    
    with pytest.raises(ValueError, match="No se puede dividir por cero"):
        divide(-1, 0)
    
    # Test divisiones exactas
    assert divide(100, 10) == 10.0
    assert divide(50, 5) == 10.0
    
    # Test divisiones con resultado decimal
    assert abs(divide(1, 3) - 0.3333333333333333) < 1e-10
    assert abs(divide(22, 7) - 3.142857142857143) < 1e-10

def test_divide_precision_flotante():
    """Test precisión en divisiones con números flotantes"""
    # Tests para verificar precision con números decimales
    resultado = divide(0.1, 0.1)
    assert abs(resultado - 1.0) < 1e-10
    
    resultado = divide(0.3, 0.1)
    assert abs(resultado - 3.0) < 1e-10


if __name__ == '__main__':
    # Ejecutar tests con unittest
    unittest.main(verbosity=2)