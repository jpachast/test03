"""
Endpoints para Test Generator
"""
from aiohttp import web
import json

test_generator_routes = web.RouteTableDef()

@test_generator_routes.post('/api/tests/generate')
async def generate_tests(request):
    """Genera tests para código dado"""
    try:
        data = await request.json()
        code = data.get('code', '')
        language = data.get('language', 'python')
        test_type = data.get('test_type', 'unit')
        
        if not code:
            return web.json_response({'success': False, 'error': 'No code provided'})
        
        from core.test_generator import get_test_generator
        generator = get_test_generator()
        
        # Analizar código
        analysis = generator.analyze_python_code(code)
        
        # Generar tests
        tests = generator.generate_python_tests(code, analysis)
        
        return web.json_response({
            'success': True,
            'analysis': analysis,
            'tests': [{'name': t.name, 'code': t.code, 'type': t.test_type, 'expected': t.expected_behavior} for t in tests],
            'count': len(tests)
        })
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

@test_generator_routes.post('/api/tests/run')
async def run_tests(request):
    """Ejecuta tests con cobertura"""
    try:
        data = await request.json()
        source_code = data.get('source_code', '')
        test_code = data.get('test_code', '')
        
        if not source_code or not test_code:
            return web.json_response({'success': False, 'error': 'Missing source_code or test_code'})
        
        from core.test_generator import get_test_generator
        generator = get_test_generator()
        
        # Ejecutar con cobertura
        coverage = await generator.run_with_coverage(source_code, test_code)
        
        return web.json_response({
            'success': True,
            'coverage': {
                'total_lines': coverage.total_lines,
                'covered_lines': coverage.covered_lines,
                'missed_lines': coverage.missed_lines,
                'coverage_percent': coverage.coverage_percent,
                'branch_coverage': coverage.branch_coverage,
                'functions_covered': coverage.functions_covered,
                'functions_missed': coverage.functions_missed
            }
        })
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

@test_generator_routes.post('/api/tests/generate-and-run')
async def generate_and_run_tests(request):
    """Genera y ejecuta tests en un solo paso"""
    try:
        data = await request.json()
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return web.json_response({'success': False, 'error': 'No code provided'})
        
        from core.test_generator import get_test_generator
        generator = get_test_generator()
        
        # Generar y ejecutar
        result = await generator.generate_and_run(code, language)
        
        return web.json_response({
            'success': True,
            'suite_id': result.suite_id,
            'tests_generated': len(result.test_cases),
            'tests_passed': sum(1 for r in result.results if r.passed),
            'tests_failed': sum(1 for r in result.results if not r.passed),
            'coverage': {
                'percent': result.coverage.coverage_percent,
                'lines': f"{result.coverage.covered_lines}/{result.coverage.total_lines}"
            },
            'results': [{'name': r.name, 'passed': r.passed, 'output': r.output[:500], 'error': r.error} for r in result.results]
        })
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})
