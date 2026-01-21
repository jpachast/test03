"""
Test Generator & Runner - Genera y ejecuta tests automáticamente
"""

import re
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TestCase:
    """Un caso de test"""
    name: str
    code: str
    expected_behavior: str
    test_type: str  # unit, integration, edge_case


@dataclass
class TestResult:
    """Resultado de ejecutar un test"""
    name: str
    passed: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class TestSuite:
    """Suite completa de tests"""
    id: str
    source_code: str
    language: str
    tests: List[TestCase] = field(default_factory=list)
    results: List[TestResult] = field(default_factory=list)
    coverage_estimate: float = 0.0
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "language": self.language,
            "tests_count": len(self.tests),
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "output": r.output[:500] if r.output else "",
                    "error": r.error,
                    "execution_time": r.execution_time
                }
                for r in self.results
            ],
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "coverage_estimate": self.coverage_estimate,
            "created_at": self.created_at
        }


class TestGenerator:
    """
    Generador automático de tests basado en análisis de código.
    """
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
        self.suites: Dict[str, TestSuite] = {}
    
    def analyze_python_code(self, code: str) -> Dict[str, Any]:
        """Analiza código Python para generar tests"""
        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": []
        }
        
        # Encontrar funciones
        func_pattern = r'def\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            params = match.group(2)
            
            # No incluir métodos privados o dunder
            if not func_name.startswith('_'):
                analysis["functions"].append({
                    "name": func_name,
                    "params": [p.strip().split(':')[0].split('=')[0].strip() 
                              for p in params.split(',') if p.strip()],
                    "has_return": bool(re.search(rf'def {func_name}.*?return\s+', code, re.DOTALL))
                })
        
        # Encontrar clases
        class_pattern = r'class\s+(\w+)\s*(?:\([^)]*\))?:'
        for match in re.finditer(class_pattern, code):
            analysis["classes"].append(match.group(1))
        
        return analysis
    
    def generate_python_tests(self, code: str, analysis: Dict[str, Any]) -> List[TestCase]:
        """Genera tests para código Python"""
        tests = []
        
        for func in analysis["functions"]:
            func_name = func["name"]
            params = func["params"]
            
            # Test básico de existencia y llamada
            if params:
                # Generar valores de prueba basados en nombres de parámetros
                test_values = []
                for p in params:
                    if 'num' in p.lower() or 'count' in p.lower() or 'n' == p.lower():
                        test_values.append("5")
                    elif 'str' in p.lower() or 'name' in p.lower() or 'text' in p.lower():
                        test_values.append('"test"')
                    elif 'list' in p.lower() or 'arr' in p.lower():
                        test_values.append("[1, 2, 3]")
                    elif 'dict' in p.lower():
                        test_values.append('{"key": "value"}')
                    elif 'bool' in p.lower() or 'flag' in p.lower():
                        test_values.append("True")
                    else:
                        test_values.append("None")
                
                args_str = ", ".join(test_values)
                
                # Test de llamada básica
                tests.append(TestCase(
                    name=f"test_{func_name}_basic_call",
                    code=f'''
{code}

# Test: llamada básica a {func_name}
try:
    result = {func_name}({args_str})
    print(f"✓ {func_name} ejecutado correctamente")
    print(f"  Resultado: {{result}}")
except Exception as e:
    print(f"✗ Error en {func_name}: {{e}}")
    raise
''',
                    expected_behavior=f"La función {func_name} debe ejecutarse sin errores",
                    test_type="unit"
                ))
                
                # Test de tipo de retorno si tiene return
                if func["has_return"]:
                    tests.append(TestCase(
                        name=f"test_{func_name}_returns_value",
                        code=f'''
{code}

# Test: verificar que {func_name} retorna algo
result = {func_name}({args_str})
assert result is not None, "{func_name} no debe retornar None"
print(f"✓ {func_name} retorna valor: {{type(result).__name__}}")
''',
                        expected_behavior=f"La función {func_name} debe retornar un valor",
                        test_type="unit"
                    ))
            else:
                # Función sin parámetros
                tests.append(TestCase(
                    name=f"test_{func_name}_no_args",
                    code=f'''
{code}

# Test: llamar {func_name} sin argumentos
try:
    result = {func_name}()
    print(f"✓ {func_name}() ejecutado correctamente")
except Exception as e:
    print(f"✗ Error: {{e}}")
    raise
''',
                    expected_behavior=f"La función {func_name} debe ejecutarse sin argumentos",
                    test_type="unit"
                ))
        
        # Test de sintaxis general
        tests.append(TestCase(
            name="test_syntax_valid",
            code=f'''
{code}

print("✓ Código tiene sintaxis válida")
''',
            expected_behavior="El código debe tener sintaxis válida",
            test_type="unit"
        ))
        
        return tests
    
    async def generate_and_run(
        self,
        code: str,
        language: str = "python"
    ) -> TestSuite:
        """Genera tests y los ejecuta"""
        import uuid
        
        suite = TestSuite(
            id=str(uuid.uuid4())[:8],
            source_code=code,
            language=language,
            created_at=datetime.now().isoformat()
        )
        
        if language == "python":
            analysis = self.analyze_python_code(code)
            suite.tests = self.generate_python_tests(code, analysis)
        else:
            # Para otros lenguajes, solo test de sintaxis
            suite.tests = [TestCase(
                name="test_syntax",
                code=code,
                expected_behavior="El código debe ejecutarse",
                test_type="unit"
            )]
        
        # Ejecutar tests
        passed = 0
        for test in suite.tests:
            result = await self.sandbox.execute_async(test.code, language, timeout=10)
            
            test_passed = result.exit_code == 0
            if test_passed:
                passed += 1
            
            suite.results.append(TestResult(
                name=test.name,
                passed=test_passed,
                output=result.stdout,
                error=result.stderr if not test_passed else None,
                execution_time=result.execution_time
            ))
        
        # Estimar coverage
        if suite.tests:
            suite.coverage_estimate = round(passed / len(suite.tests) * 100, 1)
        
        self.suites[suite.id] = suite
        return suite
    
    def get_suite(self, suite_id: str) -> Optional[TestSuite]:
        return self.suites.get(suite_id)
    
    def list_suites(self, limit: int = 20) -> List[TestSuite]:
        suites = list(self.suites.values())
        suites.sort(key=lambda x: x.created_at, reverse=True)
        return suites[:limit]


# Instancia global
_generator_instance: Optional[TestGenerator] = None


def get_test_generator(sandbox=None) -> TestGenerator:
    global _generator_instance
    if _generator_instance is None:
        if sandbox is None:
            from core.sandbox import get_sandbox
            sandbox = get_sandbox()
        _generator_instance = TestGenerator(sandbox)
    return _generator_instance
