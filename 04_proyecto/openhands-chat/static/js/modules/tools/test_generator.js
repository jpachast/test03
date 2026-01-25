/**
 * Test Generator Tool Module
 * Extracted from tools_menu_pro.js
 */
(function() {
    'use strict';

    function openTestGenerator() {
        var html = '<div style="padding: 20px;">' +
            '<p style="margin-bottom: 15px; color: #9ca3af;">Genera tests automaticamente para tu codigo Python con analisis de cobertura real.</p>' +
            '<div style="margin-bottom: 15px;">' +
                '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">Codigo a testear:</label>' +
                '<textarea id="testgen-code" placeholder="def suma(a, b):\\n    return a + b" style="width: 100%; height: 150px; padding: 10px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb; font-family: monospace; resize: vertical;"></textarea>' +
            '</div>' +
            '<div style="margin-bottom: 15px; display: flex; gap: 15px; align-items: center;">' +
                '<label style="color: #9ca3af;"><input type="checkbox" id="testgen-coverage" checked> Incluir cobertura</label>' +
                '<select id="testgen-lang" style="padding: 8px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb;">' +
                    '<option value="python">Python</option>' +
                    '<option value="javascript">JavaScript</option>' +
                '</select>' +
            '</div>' +
            '<button onclick="executeTestGen()" style="padding: 10px 20px; background: #22c55e; color: white; border: none; border-radius: 6px; cursor: pointer;">Generar y Ejecutar Tests</button>' +
            '<div id="testgen-result" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px; max-height: 400px; overflow: auto; display: none;">' +
                '<div id="testgen-output" style="color: #e5e7eb;"></div>' +
            '</div>' +
        '</div>';
        if (window.showModal) window.showModal('Test Generator', html);
    }

    async function executeTestGen() {
        var code = document.getElementById('testgen-code').value;
        if (!code.trim()) { if (window.showToast) window.showToast('Ingresa codigo para testear', 'warning'); return; }
        
        var resultDiv = document.getElementById('testgen-result');
        var outputDiv = document.getElementById('testgen-output');
        resultDiv.style.display = 'block';
        outputDiv.innerHTML = '<p style="color: #9ca3af;">⏳ Generando y ejecutando tests...</p>';
        
        try {
            var response = await fetch('/api/tests/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code,
                    language: document.getElementById('testgen-lang').value,
                    with_coverage: document.getElementById('testgen-coverage').checked
                })
            });
            var data = await response.json();
            
            if (data.suite_id || data.tests_count !== undefined) {
                var html = '<div style="margin-bottom: 15px;">' +
                    '<h4 style="color: #22c55e; margin: 0 0 10px 0;">✅ Tests Generados</h4>' +
                    '<div style="display: flex; gap: 20px; flex-wrap: wrap;">' +
                        '<span style="color: #9ca3af;">Total: <strong style="color: #e5e7eb;">' + (data.tests_count || 0) + '</strong></span>' +
                        '<span style="color: #22c55e;">Pasaron: <strong>' + (data.passed || 0) + '</strong></span>' +
                        '<span style="color: #ef4444;">Fallaron: <strong>' + (data.failed || 0) + '</strong></span>' +
                    '</div>' +
                '</div>';
                
                if (data.coverage_estimate !== undefined || data.coverage_report) {
                    html += '<div style="margin-bottom: 15px; padding: 10px; background: #111827; border-radius: 6px;">' +
                        '<h5 style="color: #3b82f6; margin: 0 0 8px 0;">📊 Cobertura</h5>' +
                        '<div style="font-size: 24px; color: #22c55e; font-weight: bold;">' + (data.coverage_estimate || 0).toFixed(1) + '%</div>' +
                    '</div>';
                }
                
                if (data.results && data.results.length > 0) {
                    html += '<div style="margin-top: 15px;"><h5 style="color: #9ca3af; margin: 0 0 8px 0;">Resultados:</h5>';
                    data.results.forEach(function(r) {
                        var icon = r.passed ? '✅' : '❌';
                        var color = r.passed ? '#22c55e' : '#ef4444';
                        html += '<div style="padding: 8px; margin: 4px 0; background: #111827; border-radius: 4px; border-left: 3px solid ' + color + ';">' +
                            '<span>' + icon + ' ' + r.name + '</span>' +
                            (r.error ? '<pre style="color: #ef4444; font-size: 11px; margin: 5px 0 0 0;">' + r.error + '</pre>' : '') +
                        '</div>';
                    });
                    html += '</div>';
                }
                
                outputDiv.innerHTML = html;
                if (window.showToast) window.showToast('Tests generados: ' + (data.passed || 0) + '/' + (data.tests_count || 0) + ' pasaron', 'success');
            } else if (data.detail) {
                outputDiv.innerHTML = '<p style="color: #ef4444;">Error: ' + data.detail + '</p>';
            } else {
                outputDiv.innerHTML = '<pre style="color: #e5e7eb;">' + JSON.stringify(data, null, 2) + '</pre>';
            }
        } catch (e) {
            outputDiv.innerHTML = '<p style="color: #ef4444;">Error: ' + e.message + '</p>';
        }
    }

    window.TestGeneratorTool = { open: openTestGenerator, execute: executeTestGen };
    window.openTestGenerator = openTestGenerator;
    window.executeTestGen = executeTestGen;
})();
