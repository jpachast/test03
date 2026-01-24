import pytest
from factorial import factorial

class TestFactorial:
    """Tests completos para la función factorial"""
    
    def test_factorial_casos_base(self):
        """Test casos base: 0! = 1, 1! = 1"""
        assert factorial(0) == 1
        assert factorial(1) == 1
    
    def test_factorial_numeros_pequenos(self):
        """Test números pequeños conocidos"""
        assert factorial(2) == 2
        assert factorial(3) == 6
        assert factorial(4) == 24
        assert factorial(5) == 120
    
    def test_factorial_numeros_medianos(self):
        """Test números medianos"""
        assert factorial(6) == 720
        assert factorial(7) == 5040
        assert factorial(8) == 40320
        assert factorial(10) == 3628800
    
    def test_factorial_numero_grande(self):
        """Test número grande"""
        # 12! = 479,001,600
        assert factorial(12) == 479001600
    
    def test_factorial_secuencia(self):
        """Test secuencia de factoriales"""
        expected = [1, 1, 2, 6, 24, 120, 720, 5040]
        for i, exp in enumerate(expected):
            assert factorial(i) == exp
    
    def test_factorial_negativos_comportamiento(self):
        """Test comportamiento con números negativos"""
        # Según tu implementación, números negativos devuelven 1
        assert factorial(-1) == 1
        assert factorial(-5) == 1
        assert factorial(-100) == 1
    
    def test_factorial_tipo_resultado(self):
        """Test que el resultado sea entero"""
        result = factorial(5)
        assert isinstance(result, int)
        assert result == 120
    
    def test_factorial_casos_limite(self):
        """Test casos límite específicos"""
        # Factorial de 0 (caso especial matemático)
        assert factorial(0) == 1
        
        # Factorial de 1 (identidad)
        assert factorial(1) == 1
        
        # Factorial de número par e impar
        assert factorial(4) == 24  # par
        assert factorial(5) == 120  # impar

# Tests parametrizados para mayor cobertura
@pytest.mark.parametrize("n,expected", [
    (0, 1),
    (1, 1),
    (2, 2),
    (3, 6),
    (4, 24),
    (5, 120),
    (6, 720),
    (7, 5040),
    (8, 40320),
    (9, 362880),
    (10, 3628800)
])
def test_factorial_parametrizado(n, expected):
    """Test parametrizado con casos conocidos"""
    assert factorial(n) == expected

# Test de rendimiento básico
def test_factorial_rendimiento_basico():
    """Test que la función no sea extremadamente lenta"""
    import time
    
    start = time.time()
    result = factorial(15)
    end = time.time()
    
    # Debería completarse en menos de 1 segundo
    assert (end - start) < 1.0
    assert result == 1307674368000

if __name__ == "__main__":
    # Ejecutar tests básicos si se ejecuta directamente
    print("🧪 Ejecutando tests de factorial...")
    
    # Tests manuales rápidos
    test_cases = [0, 1, 2, 3, 4, 5, 10]
    expected = [1, 1, 2, 6, 24, 120, 3628800]
    
    print("\n📊 Resultados:")
    for i, (n, exp) in enumerate(zip(test_cases, expected)):
        result = factorial(n)
        status = "✅" if result == exp else "❌"
        print(f"{status} factorial({n}) = {result} (esperado: {exp})")
    
    print("\n🎯 Tests completados!")