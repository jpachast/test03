/**
 * Tools Menu Pro - Reemplazo completo del menu de herramientas
 * Intercepta el menu antiguo y lo reemplaza con version profesional
 */

(function() {
    // Esperar a que el DOM este listo
    function init() {
        console.log('[ToolsMenuPro] Inicializando...');
        
        // Ocultar menu antiguo permanentemente
        const oldMenu = document.getElementById('toolsMenu');
        if (oldMenu) {
            oldMenu.style.display = 'none';
            oldMenu.remove();
            console.log('[ToolsMenuPro] Menu antiguo eliminado');
        }
        
        // Sobrescribir la funcion toggleToolsMenu
        window.toggleToolsMenu = function() {
            window.toolsMenuPro.toggle();
        };
        
        // Crear instancia
        window.toolsMenuPro = new ToolsMenuPro();
        console.log('[ToolsMenuPro] Listo!');
    }

    class ToolsMenuPro {
        constructor() {
            this.isOpen = false;
            this.menuElement = null;
        }

        toggle() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        }

        open() {
            if (this.menuElement) {
                this.menuElement.remove();
            }

            const toolsBtn = document.querySelector('.tools-btn');
            if (!toolsBtn) return;

            const rect = toolsBtn.getBoundingClientRect();

            this.menuElement = document.createElement('div');
            this.menuElement.className = 'tools-menu-pro';
            this.menuElement.innerHTML = this.getMenuHTML();

            Object.assign(this.menuElement.style, {
                position: 'fixed',
                left: rect.left + 'px',
                bottom: (window.innerHeight - rect.top + 8) + 'px',
                zIndex: '999999',
                opacity: '0',
                transform: 'translateY(10px) scale(0.95)',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
            });

            document.body.appendChild(this.menuElement);

            // Animar entrada
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    this.menuElement.style.opacity = '1';
                    this.menuElement.style.transform = 'translateY(0) scale(1)';
                });
            });

            this.isOpen = true;

            // Cerrar al hacer clic fuera
            setTimeout(() => {
                document.addEventListener('click', this.handleOutsideClick);
            }, 10);
        }

        handleOutsideClick = (e) => {
            if (this.isOpen && !e.target.closest('.tools-menu-pro') && !e.target.closest('.tools-btn')) {
                this.close();
            }
        }

        close() {
            document.removeEventListener('click', this.handleOutsideClick);
            
            if (this.menuElement) {
                this.menuElement.style.opacity = '0';
                this.menuElement.style.transform = 'translateY(10px) scale(0.95)';
                setTimeout(() => {
                    if (this.menuElement) {
                        this.menuElement.remove();
                        this.menuElement = null;
                    }
                }, 200);
            }
            this.isOpen = false;
        }

        exec(action) {
            this.close();
            setTimeout(() => {
                try {
                    if (typeof window[action] === 'function') {
                        window[action]();
                    } else {
                        eval(action);
                    }
                } catch(e) {
                    console.error('[ToolsMenuPro] Error:', action, e);
                    if (typeof showToast === 'function') {
                        showToast('Error: ' + e.message, 'error');
                    }
                }
            }, 250);
        }

        execFromData(btn) {
            var action = btn.getAttribute('data-action');
            this.exec(action);
        }

        getMenuHTML() {
            const sections = [
                {
                    title: 'Multi-Agent AI',
                    items: [
                        { icon: '🤖', label: 'Multi-Agent Rapido', action: "runMultiAgent('quick')", desc: '3 agentes en paralelo', color: '#a855f7' },
                        { icon: '🧠', label: 'Multi-Agent Completo', action: "runMultiAgent('full')", desc: '5 agentes + seguridad', color: '#8b5cf6' }
                    ]
                },
                {
                    title: 'Analisis de Codigo',
                    items: [
                        { icon: '🧪', label: 'Test Generator', action: 'openTestGenerator()', desc: 'Tests + cobertura real', color: '#22c55e' },
                        { icon: '🔍', label: 'Semantic Search', action: 'openSemanticSearch()', desc: 'Busqueda con embeddings', color: '#3b82f6' },
                        { icon: '🕷️', label: 'Web Scraper', action: 'openWebScraper()', desc: 'Extraer datos web', color: '#dc2626' },
                        { icon: '🗺️', label: 'Codemaps', action: 'openCodemaps()', desc: 'Grafo AST interactivo', color: '#f59e0b' },
                        { icon: '🎨', label: 'Code Parser', action: 'openCodeParser()', desc: 'AST y autocompletado', color: '#ec4899' },
                    ]
                },
                {
                    title: 'Herramientas Git',
                    items: [
                        { icon: '📊', label: 'Diff Preview', action: 'openDiffPreview()', desc: 'Cambios estilo GitHub', color: '#ef4444' },
                        { icon: '📸', label: 'Checkpoints', action: 'openCheckpoints()', desc: 'Snapshots del proyecto', color: '#06b6d4' }
                    ]
                },
                {
                    title: 'Automatizacion',
                    items: [
                        { icon: '🔧', label: 'Auto-Fix', action: 'openAutoFix()', desc: 'Detectar y corregir', color: '#f97316' },
                        { icon: '⚡', label: 'Background Agents', action: 'openBackgroundAgents()', desc: 'Tareas en paralelo', color: '#eab308' },
                        { icon: '🎯', label: 'MCTS Optimizer', action: 'openMCTSOptimizer()', desc: 'Monte Carlo Search', color: '#14b8a6' }
                    ]
                },
                {
                    title: 'Avanzado',
                    items: [
                        { icon: '🔗', label: 'MCP Protocol', action: 'openMCPProtocol()', desc: 'Contexto del LLM', color: '#6366f1' },
                        { icon: 'ℹ️', label: 'Info Herramientas', action: 'showToolsInfo()', desc: 'Ver documentacion', color: '#64748b' }
                    ]
                }
            ];

            let html = `<div style="
                background: linear-gradient(180deg, #1a1a2e 0%, #16162a 100%);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05);
                min-width: 320px;
                max-height: 75vh;
                overflow-y: auto;
                overflow-x: hidden;
            ">`;
            
            // Header
            html += `<div style="
                padding: 16px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px 16px 0 0;
                display: flex;
                align-items: center;
                gap: 10px;
                position: sticky;
                top: 0;
                z-index: 10;
            ">
                <span style="font-size: 24px;">🔧</span>
                <div>
                    <div style="color: white; font-weight: 700; font-size: 16px;">Herramientas Pro</div>
                    <div style="color: rgba(255,255,255,0.7); font-size: 11px;">14 herramientas disponibles</div>
                </div>
            </div>`;

            // Sections
            html += '<div style="padding: 8px;">';
            
            sections.forEach((section, sIdx) => {
                html += `<div style="
                    padding: 8px 12px 4px;
                    color: #9ca3af;
                    font-size: 10px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    ${sIdx > 0 ? 'margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;' : ''}
                ">${section.title}</div>`;
                
                section.items.forEach(item => {
                    html += `<button data-action="${item.action}" onclick="toolsMenuPro.execFromData(this)" style="
                        width: 100%;
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        padding: 10px 12px;
                        background: transparent;
                        border: none;
                        border-radius: 10px;
                        cursor: pointer;
                        transition: all 0.15s ease;
                        text-align: left;
                        margin: 2px 0;
                    " onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='transparent'">
                        <div style="
                            width: 36px;
                            height: 36px;
                            background: ${item.color}20;
                            border-radius: 10px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 18px;
                        ">${item.icon}</div>
                        <div style="flex: 1; min-width: 0;">
                            <div style="color: #e5e7eb; font-size: 13px; font-weight: 500;">${item.label}</div>
                            <div style="color: #6b7280; font-size: 11px; margin-top: 1px;">${item.desc}</div>
                        </div>
                        <span style="color: #4b5563; font-size: 16px;">›</span>
                    </button>`;
                });
            });

            html += '</div></div>';
            return html;
        }
    }

    // Iniciar cuando el DOM este listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 100);
    }
})();



// WEB SCRAPER FUNCTIONS
function openWebScraper() {
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Extrae datos de paginas web: titulo, texto, links, imagenes y tablas.</p>' +
        '<div style="margin-bottom: 15px;">' +
            '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">URL a extraer:</label>' +
            '<input type="text" id="scraper-url" placeholder="https://ejemplo.com" style="width: 100%; padding: 10px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb;">' +
        '</div>' +
        '<div style="margin-bottom: 15px; display: flex; gap: 15px; flex-wrap: wrap;">' +
            '<label style="color: #9ca3af;"><input type="checkbox" id="scraper-links" checked> Extraer links</label>' +
            '<label style="color: #9ca3af;"><input type="checkbox" id="scraper-images"> Extraer imagenes</label>' +
            '<label style="color: #9ca3af;"><input type="checkbox" id="scraper-tables"> Extraer tablas</label>' +
        '</div>' +
        '<button onclick="executeScrape()" style="padding: 10px 20px; background: #dc2626; color: white; border: none; border-radius: 6px; cursor: pointer;">Extraer Datos</button>' +
        '<div id="scraper-result" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px; max-height: 300px; overflow: auto; display: none;">' +
            '<pre id="scraper-output" style="color: #e5e7eb; white-space: pre-wrap; margin: 0;"></pre>' +
        '</div>' +
    '</div>';
    showModal('Web Scraper', html);
}

async function executeScrape() {
    var url = document.getElementById('scraper-url').value;
    if (!url) { showToast('Ingresa una URL', 'warning'); return; }
    var resultDiv = document.getElementById('scraper-result');
    var outputPre = document.getElementById('scraper-output');
    resultDiv.style.display = 'block';
    outputPre.textContent = 'Extrayendo datos...';
    try {
        var response = await fetch('/api/scraper/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                extract_links: document.getElementById('scraper-links').checked,
                extract_images: document.getElementById('scraper-images').checked,
                extract_tables: document.getElementById('scraper-tables').checked
            })
        });
        var data = await response.json();
        if (data.success) {
            var content = (data.text_content || '').substring(0, 500);
            outputPre.textContent = 'Titulo: ' + (data.title || 'N/A') + '\n\nContenido (500 chars):\n' + content + '...\n\nLinks: ' + (data.links || []).length + '\nImagenes: ' + (data.images || []).length + '\nTablas: ' + (data.tables || []).length;
            showToast('Datos extraidos', 'success');
        } else {
            outputPre.textContent = 'Error: ' + (data.error || 'Error');
        }
    } catch (e) { outputPre.textContent = 'Error: ' + e.message; }
}

// TEST GENERATOR FUNCTIONS
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
    showModal('Test Generator', html);
}

async function executeTestGen() {
    var code = document.getElementById('testgen-code').value;
    if (!code.trim()) { showToast('Ingresa codigo para testear', 'warning'); return; }
    
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
            showToast('Tests generados: ' + (data.passed || 0) + '/' + (data.tests_count || 0) + ' pasaron', 'success');
        } else if (data.detail) {
            outputDiv.innerHTML = '<p style="color: #ef4444;">Error: ' + data.detail + '</p>';
        } else {
            outputDiv.innerHTML = '<pre style="color: #e5e7eb;">' + JSON.stringify(data, null, 2) + '</pre>';
        }
    } catch (e) {
        outputDiv.innerHTML = '<p style="color: #ef4444;">Error: ' + e.message + '</p>';
    }
}

// MULTI-AGENT FUNCTIONS
function runMultiAgent(mode) {
    var title = mode === 'quick' ? 'Multi-Agent Rapido' : 'Multi-Agent Completo';
    var desc = mode === 'quick' 
        ? '3 agentes en paralelo: Reviewer, Tester, Documenter' 
        : '5 agentes + seguridad: Reviewer, Tester, Documenter, Security, Architect';
    
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">' + desc + '</p>' +
        '<div style="margin-bottom: 15px;">' +
            '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">Codigo a analizar:</label>' +
            '<textarea id="multiagent-code" placeholder="def ejemplo():\\n    pass" style="width: 100%; height: 150px; padding: 10px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb; font-family: monospace;"></textarea>' +
        '</div>' +
        '<div style="margin-bottom: 15px;">' +
            '<select id="multiagent-lang" style="padding: 8px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb;">' +
                '<option value="python">Python</option>' +
                '<option value="javascript">JavaScript</option>' +
            '</select>' +
        '</div>' +
        '<button onclick="executeMultiAgent(\'' + mode + '\')" style="padding: 10px 20px; background: #8b5cf6; color: white; border: none; border-radius: 6px; cursor: pointer;">Ejecutar Agentes</button>' +
        '<div id="multiagent-result" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px; max-height: 400px; overflow: auto; display: none;">' +
            '<div id="multiagent-output" style="color: #e5e7eb;"></div>' +
        '</div>' +
    '</div>';
    showModal(title, html);
}

async function executeMultiAgent(mode) {
    var code = document.getElementById('multiagent-code').value;
    if (!code.trim()) { showToast('Ingresa codigo para analizar', 'warning'); return; }
    
    var resultDiv = document.getElementById('multiagent-result');
    var outputDiv = document.getElementById('multiagent-output');
    resultDiv.style.display = 'block';
    outputDiv.innerHTML = '<p style="color: #9ca3af;">⏳ Ejecutando agentes en paralelo...</p>';
    
    var endpoint = mode === 'quick' ? '/api/advanced/multiagent/quick-review' : '/api/advanced/multiagent/full-analysis';
    
    try {
        var response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: document.getElementById('multiagent-lang').value
            })
        });
        var data = await response.json();
        
        if (data.session_id || data.results || data.agents_results) {
            var results = data.agents_results || data.results || [];
            var html = '<div style="margin-bottom: 15px;">' +
                '<h4 style="color: #8b5cf6; margin: 0 0 10px 0;">✅ Analisis Completado</h4>' +
                '<div style="color: #9ca3af;">Session: ' + (data.session_id || 'N/A') + '</div>' +
                '<div style="color: #9ca3af;">Agentes: ' + (results.length || Object.keys(results).length || 0) + '</div>' +
            '</div>';
            
            // Mostrar resultados de cada agente
            if (Array.isArray(results)) {
                results.forEach(function(r) {
                    html += renderAgentResult(r);
                });
            } else if (typeof results === 'object') {
                Object.keys(results).forEach(function(role) {
                    html += renderAgentResult({role: role, response: results[role]});
                });
            }
            
            outputDiv.innerHTML = html;
            showToast('Analisis completado', 'success');
        } else if (data.detail) {
            outputDiv.innerHTML = '<p style="color: #ef4444;">Error: ' + data.detail + '</p>';
        } else {
            outputDiv.innerHTML = '<pre style="color: #e5e7eb; white-space: pre-wrap;">' + JSON.stringify(data, null, 2) + '</pre>';
        }
    } catch (e) {
        outputDiv.innerHTML = '<p style="color: #ef4444;">Error: ' + e.message + '</p>';
    }
}

function renderAgentResult(r) {
    var roleColors = {
        'reviewer': '#3b82f6',
        'tester': '#22c55e', 
        'documenter': '#f59e0b',
        'security': '#ef4444',
        'architect': '#8b5cf6'
    };
    var roleIcons = {
        'reviewer': '🔍',
        'tester': '🧪',
        'documenter': '📝',
        'security': '🔒',
        'architect': '🏗️'
    };
    var role = (r.role || r.agent || 'agent').toLowerCase();
    var color = roleColors[role] || '#6b7280';
    var icon = roleIcons[role] || '🤖';
    var content = r.response || r.result || r.output || JSON.stringify(r);
    if (typeof content === 'object') content = JSON.stringify(content, null, 2);
    content = (content || '').substring(0, 500);
    
    return '<div style="margin: 10px 0; padding: 12px; background: #111827; border-radius: 8px; border-left: 3px solid ' + color + ';">' +
        '<div style="font-weight: bold; color: ' + color + '; margin-bottom: 8px;">' + icon + ' ' + role.toUpperCase() + '</div>' +
        '<pre style="color: #d1d5db; white-space: pre-wrap; font-size: 12px; margin: 0;">' + content + '</pre>' +
    '</div>';
}

// MCTS OPTIMIZER FUNCTIONS
// DIFF PREVIEW FUNCTIONS
function openDiffPreview() {
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Visualiza cambios de Git con estilo GitHub.</p>' +
        '<div style="margin-bottom: 15px; display: flex; gap: 10px;">' +
            '<button onclick="loadDiffStaged()" style="flex: 1; padding: 10px; background: #22c55e; color: white; border: none; border-radius: 6px; cursor: pointer;">Staged</button>' +
            '<button onclick="loadDiffUnstaged()" style="flex: 1; padding: 10px; background: #f59e0b; color: white; border: none; border-radius: 6px; cursor: pointer;">Unstaged</button>' +
            '<button onclick="loadDiffStatus()" style="flex: 1; padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">Status</button>' +
        '</div>' +
        '<div id="diff-result" style="background: #0d1117; border-radius: 8px; overflow: hidden; max-height: 450px; overflow-y: auto;">' +
            '<div id="diff-output" style="padding: 15px; color: #c9d1d9;"><p style="color: #8b949e; text-align: center;">Selecciona una opcion para ver los cambios</p></div>' +
        '</div>' +
    '</div>';
    showModal('Diff Preview', html);
}

async function loadDiffStaged() {
    var outputDiv = document.getElementById('diff-output');
    outputDiv.innerHTML = '<p style="color: #8b949e;">⏳ Cargando cambios staged...</p>';
    try {
        var response = await fetch('/api/diff/staged', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace: '/workspace/project/test03' })
        });
        var data = await response.json();
        renderDiff(data);
    } catch (e) {
        outputDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function loadDiffUnstaged() {
    var outputDiv = document.getElementById('diff-output');
    outputDiv.innerHTML = '<p style="color: #8b949e;">⏳ Cargando cambios unstaged...</p>';
    try {
        var response = await fetch('/api/diff/unstaged', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace: '/workspace/project/test03' })
        });
        var data = await response.json();
        renderDiff(data);
    } catch (e) {
        outputDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function loadDiffStatus() {
    var outputDiv = document.getElementById('diff-output');
    outputDiv.innerHTML = '<p style="color: #8b949e;">⏳ Cargando status...</p>';
    try {
        var response = await fetch('/api/diff/status?workspace=/workspace/project/test03');
        var data = await response.json();
        renderStatus(data);
    } catch (e) {
        outputDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

function renderDiff(data) {
    var outputDiv = document.getElementById('diff-output');
    if (!data.files || data.files.length === 0) {
        outputDiv.innerHTML = '<p style="color: #8b949e; text-align: center;">No hay cambios para mostrar</p>';
        return;
    }
    
    var html = '<div style="margin-bottom: 10px; padding: 10px; background: #161b22; border-radius: 6px;">' +
        '<span style="color: #8b949e;">Archivos: </span><strong style="color: #c9d1d9;">' + data.files.length + '</strong>' +
        '<span style="margin-left: 15px; color: #3fb950;">+' + (data.total_additions || 0) + '</span>' +
        '<span style="margin-left: 10px; color: #f85149;">-' + (data.total_deletions || 0) + '</span>' +
    '</div>';
    
    data.files.forEach(function(file) {
        var statusColor = file.status === 'added' ? '#3fb950' : (file.status === 'deleted' ? '#f85149' : '#d29922');
        var statusIcon = file.status === 'added' ? '+' : (file.status === 'deleted' ? '-' : '~');
        
        html += '<div style="margin-bottom: 10px; border: 1px solid #30363d; border-radius: 6px; overflow: hidden;">' +
            '<div style="padding: 10px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 10px;">' +
                '<span style="color: ' + statusColor + '; font-weight: bold;">' + statusIcon + '</span>' +
                '<span style="color: #c9d1d9; font-family: monospace;">' + file.file + '</span>' +
                '<span style="margin-left: auto; color: #3fb950; font-size: 12px;">+' + (file.additions || 0) + '</span>' +
                '<span style="color: #f85149; font-size: 12px;">-' + (file.deletions || 0) + '</span>' +
            '</div>';
        
        if (file.chunks && file.chunks.length > 0) {
            html += '<div style="font-family: monospace; font-size: 12px;">';
            file.chunks.forEach(function(chunk) {
                html += '<div style="padding: 5px 10px; background: #161b22; color: #8b949e; border-bottom: 1px solid #21262d;">' + escapeHtml(chunk.header) + '</div>';
                if (chunk.lines) {
                    chunk.lines.forEach(function(line) {
                        var bgColor = '#0d1117';
                        var textColor = '#c9d1d9';
                        if (line.type === 'add') { bgColor = '#0d2818'; textColor = '#3fb950'; }
                        else if (line.type === 'del') { bgColor = '#3d1515'; textColor = '#f85149'; }
                        html += '<div style="padding: 2px 10px; background: ' + bgColor + '; color: ' + textColor + '; white-space: pre;">' + escapeHtml(line.content || '') + '</div>';
                    });
                }
            });
            html += '</div>';
        }
        html += '</div>';
    });
    
    outputDiv.innerHTML = html;
}

function renderStatus(data) {
    var outputDiv = document.getElementById('diff-output');
    
    // Extraer archivos de la estructura correcta
    var files = data.files || {};
    var staged = files.staged || [];
    var unstaged = files.unstaged || [];
    var untracked = files.untracked || [];
    
    var html = '<div style="padding: 10px;">' +
        '<div style="margin-bottom: 15px; padding: 10px; background: #161b22; border-radius: 6px; display: flex; justify-content: space-between;">' +
            '<span style="color: #8b949e;">📁 Status del Repositorio</span>' +
            '<span style="color: #3fb950;">' + staged.length + ' staged</span>' +
            '<span style="color: #d29922;">' + unstaged.length + ' modified</span>' +
            '<span style="color: #8b949e;">' + untracked.length + ' untracked</span>' +
        '</div>';

    if (staged.length > 0) {
        html += '<div style="margin-bottom: 15px;"><div style="color: #3fb950; margin-bottom: 8px; font-weight: bold; display: flex; align-items: center; gap: 8px;">✅ Staged (' + staged.length + ')</div>';
        staged.forEach(function(f) {
            var fname = (typeof f === 'object') ? f.file : f;
            html += '<div style="padding: 8px 12px; background: #0d2818; border-radius: 4px; margin: 4px 0; color: #3fb950; font-family: monospace; font-size: 12px; display: flex; align-items: center; gap: 8px;"><span style="color: #238636;">+</span>' + fname + '</div>';
        });
        html += '</div>';
    }

    if (unstaged.length > 0) {
        html += '<div style="margin-bottom: 15px;"><div style="color: #d29922; margin-bottom: 8px; font-weight: bold; display: flex; align-items: center; gap: 8px;">📝 Modificados (' + unstaged.length + ')</div>';
        unstaged.forEach(function(f) {
            var fname = (typeof f === 'object') ? f.file : f;
            html += '<div style="padding: 8px 12px; background: #2d2006; border-radius: 4px; margin: 4px 0; color: #d29922; font-family: monospace; font-size: 12px; display: flex; align-items: center; gap: 8px;"><span style="color: #d29922;">~</span>' + fname + '</div>';
        });
        html += '</div>';
    }

    if (untracked.length > 0) {
        html += '<div style="margin-bottom: 15px;"><div style="color: #8b949e; margin-bottom: 8px; font-weight: bold; display: flex; align-items: center; gap: 8px;">❓ Sin seguimiento (' + untracked.length + ')</div>';
        untracked.slice(0, 10).forEach(function(f) {
            var fname = (typeof f === 'object') ? f.file : f;
            html += '<div style="padding: 8px 12px; background: #161b22; border: 1px solid #30363d; border-radius: 4px; margin: 4px 0; color: #8b949e; font-family: monospace; font-size: 12px; display: flex; align-items: center; gap: 8px;"><span style="color: #f85149;">?</span>' + fname + '</div>';
        });
        if (untracked.length > 10) {
            html += '<div style="padding: 8px; color: #6e7681; text-align: center;">... y ' + (untracked.length - 10) + ' archivos más</div>';
        }
        html += '</div>';
    }

    if (staged.length === 0 && unstaged.length === 0 && untracked.length === 0) {
        html += '<div style="padding: 30px; text-align: center;"><span style="font-size: 48px;">✨</span><p style="color: #3fb950; margin-top: 10px;">Working tree clean</p></div>';
    }

    html += '</div>';
    outputDiv.innerHTML = html;
}    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// MCP PROTOCOL FUNCTIONS - Implementación Real
function openMCPProtocol() {
    var convId = window.currentConversationId || 29;
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Model Context Protocol - Gestiona el contexto del LLM.</p>' +
        '<div style="display: flex; gap: 10px; margin-bottom: 15px;">' +
            '<button onclick="loadMCPSession(' + convId + ')" style="flex: 1; padding: 10px; background: #6366f1; color: white; border: none; border-radius: 6px; cursor: pointer;">📋 Ver Contexto</button>' +
            '<button onclick="showAddContextForm(' + convId + ')" style="flex: 1; padding: 10px; background: #22c55e; color: white; border: none; border-radius: 6px; cursor: pointer;">➕ Agregar</button>' +
            '<button onclick="getMCPStatus()" style="flex: 1; padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">📊 Status</button>' +
        '</div>' +
        '<div id="mcp-form-area" style="display: none; margin-bottom: 15px; padding: 15px; background: #1f2937; border-radius: 8px;"></div>' +
        '<div id="mcp-result" style="background: #0d1117; border-radius: 8px; padding: 15px; max-height: 400px; overflow-y: auto;">' +
            '<p style="color: #8b949e; text-align: center;">Selecciona una opcion para ver/gestionar el contexto</p>' +
        '</div>' +
    '</div>';
    showModal('MCP Protocol', html);
}

async function loadMCPSession(convId) {
    var resultDiv = document.getElementById('mcp-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Cargando contexto...</p>';
    try {
        var response = await fetch('/api/mcp/session/' + convId);
        var data = await response.json();
        renderMCPSession(data);
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

function renderMCPSession(data) {
    var resultDiv = document.getElementById('mcp-result');
    if (!data.contexts || data.contexts.length === 0) {
        resultDiv.innerHTML = '<div style="text-align: center; padding: 20px;">' +
            '<p style="color: #8b949e; margin-bottom: 15px;">No hay contexto configurado</p>' +
            '<p style="color: #6b7280; font-size: 12px;">Agrega contexto de sistema, archivos o memoria para mejorar las respuestas del LLM</p>' +
        '</div>';
        return;
    }
    
    var html = '<div style="margin-bottom: 10px; padding: 10px; background: #161b22; border-radius: 6px;">' +
        '<span style="color: #8b949e;">Conversation: </span><strong style="color: #6366f1;">#' + data.conversation_id + '</strong>' +
        '<span style="margin-left: 15px; color: #8b949e;">Items: </span><strong style="color: #c9d1d9;">' + data.contexts.length + '</strong>' +
        '<span style="margin-left: 15px; color: #8b949e;">Tokens: </span><strong style="color: #f59e0b;">~' + (data.total_tokens || 0) + '</strong>' +
    '</div>';
    
    var typeColors = {
        'system': '#ef4444', 'project': '#f59e0b', 'file': '#22c55e',
        'conversation': '#3b82f6', 'tool_result': '#8b5cf6', 'memory': '#ec4899', 'preference': '#14b8a6'
    };
    var typeIcons = {
        'system': '⚙️', 'project': '📁', 'file': '📄',
        'conversation': '💬', 'tool_result': '🔧', 'memory': '🧠', 'preference': '⭐'
    };
    
    data.contexts.forEach(function(ctx) {
        var color = typeColors[ctx.type] || '#6b7280';
        var icon = typeIcons[ctx.type] || '📌';
        html += '<div style="margin-bottom: 8px; border: 1px solid #30363d; border-radius: 6px; overflow: hidden;">' +
            '<div style="padding: 10px; background: #161b22; display: flex; align-items: center; gap: 10px;">' +
                '<span>' + icon + '</span>' +
                '<span style="color: ' + color + '; font-weight: bold; text-transform: uppercase; font-size: 11px;">' + ctx.type + '</span>' +
                '<span style="color: #6b7280; font-size: 11px;">P:' + ctx.priority + '</span>' +
                '<span style="margin-left: auto; color: #6b7280; font-size: 10px;">' + (ctx.id || '').substring(0, 8) + '</span>' +
                '<button onclick="removeMCPContext(' + data.conversation_id + ', \'' + ctx.id + '\')" style="background: #dc2626; color: white; border: none; padding: 3px 8px; border-radius: 4px; cursor: pointer; font-size: 10px;">✕</button>' +
            '</div>' +
            '<div style="padding: 10px; background: #0d1117; color: #c9d1d9; font-size: 12px; font-family: monospace; white-space: pre-wrap; max-height: 100px; overflow: auto;">' + escapeHtmlMCP(ctx.content || '') + '</div>' +
        '</div>';
    });
    
    resultDiv.innerHTML = html;
}

function showAddContextForm(convId) {
    var formArea = document.getElementById('mcp-form-area');
    formArea.style.display = 'block';
    formArea.innerHTML = '<div>' +
        '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">Tipo de Contexto:</label>' +
        '<select id="mcp-ctx-type" style="width: 100%; padding: 8px; background: #374151; border: 1px solid #4b5563; border-radius: 6px; color: #e5e7eb; margin-bottom: 10px;">' +
            '<option value="system">⚙️ System - Instrucciones base</option>' +
            '<option value="project">📁 Project - Info del proyecto</option>' +
            '<option value="file">📄 File - Contenido de archivo</option>' +
            '<option value="memory">🧠 Memory - Recordatorio</option>' +
            '<option value="preference">⭐ Preference - Preferencia usuario</option>' +
        '</select>' +
        '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">Contenido:</label>' +
        '<textarea id="mcp-ctx-content" placeholder="Escribe el contexto aqui..." style="width: 100%; height: 80px; padding: 10px; background: #374151; border: 1px solid #4b5563; border-radius: 6px; color: #e5e7eb; font-family: monospace; margin-bottom: 10px;"></textarea>' +
        '<div style="display: flex; gap: 10px;">' +
            '<div style="flex: 1;">' +
                '<label style="display: block; margin-bottom: 5px; color: #9ca3af; font-size: 12px;">Prioridad (1-10):</label>' +
                '<input type="number" id="mcp-ctx-priority" value="5" min="1" max="10" style="width: 100%; padding: 8px; background: #374151; border: 1px solid #4b5563; border-radius: 6px; color: #e5e7eb;">' +
            '</div>' +
            '<div style="flex: 2; display: flex; align-items: end; gap: 10px;">' +
                '<button onclick="addMCPContext(' + convId + ')" style="flex: 1; padding: 10px; background: #22c55e; color: white; border: none; border-radius: 6px; cursor: pointer;">Agregar</button>' +
                '<button onclick="document.getElementById(\'mcp-form-area\').style.display=\'none\'" style="padding: 10px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer;">Cancelar</button>' +
            '</div>' +
        '</div>' +
    '</div>';
}

async function addMCPContext(convId) {
    var ctxType = document.getElementById('mcp-ctx-type').value;
    var content = document.getElementById('mcp-ctx-content').value;
    var priority = parseInt(document.getElementById('mcp-ctx-priority').value) || 5;
    
    if (!content.trim()) { showToast('El contenido es requerido', 'warning'); return; }
    
    var resultDiv = document.getElementById('mcp-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Agregando contexto...</p>';
    
    try {
        var response = await fetch('/api/mcp/context/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: convId,
                context_type: ctxType,
                content: content,
                priority: priority,
                metadata: {}
            })
        });
        var data = await response.json();
        
        if (data.success) {
            showToast('Contexto agregado: ' + ctxType, 'success');
            document.getElementById('mcp-form-area').style.display = 'none';
            loadMCPSession(convId);
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'Error desconocido') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function removeMCPContext(convId, contextId) {
    if (!confirm('¿Eliminar este contexto?')) return;
    
    try {
        var response = await fetch('/api/mcp/context/' + convId + '/' + contextId, { method: 'DELETE' });
        var data = await response.json();
        
        if (data.success) {
            showToast('Contexto eliminado', 'success');
            loadMCPSession(convId);
        } else {
            showToast('Error: ' + (data.detail || 'No se pudo eliminar'), 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function getMCPStatus() {
    var resultDiv = document.getElementById('mcp-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Obteniendo status...</p>';
    
    try {
        var response = await fetch('/api/mcp/status');
        var data = await response.json();
        
        var html = '<div style="padding: 15px;">' +
            '<h4 style="color: #6366f1; margin: 0 0 15px 0;">📊 MCP Status</h4>' +
            '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">' +
                '<div style="padding: 15px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 12px;">Sesiones Activas</div>' +
                    '<div style="font-size: 28px; color: #6366f1; font-weight: bold;">' + (data.active_sessions || 0) + '</div>' +
                '</div>' +
                '<div style="padding: 15px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 12px;">Total Contextos</div>' +
                    '<div style="font-size: 28px; color: #22c55e; font-weight: bold;">' + (data.total_contexts || 0) + '</div>' +
                '</div>' +
                '<div style="padding: 15px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 12px;">Tokens Usados</div>' +
                    '<div style="font-size: 28px; color: #f59e0b; font-weight: bold;">' + (data.total_tokens || 0) + '</div>' +
                '</div>' +
                '<div style="padding: 15px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 12px;">Estado</div>' +
                    '<div style="font-size: 18px; color: #22c55e; font-weight: bold;">' + (data.status || 'active') + '</div>' +
                '</div>' +
            '</div>' +
        '</div>';
        
        resultDiv.innerHTML = html;
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

function escapeHtmlMCP(text) {
    if (!text) return '';
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// SEMANTIC SEARCH / CODE EMBEDDINGS FUNCTIONS
function openSemanticSearch() {
    var workspace = '/workspace/project/test03';
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Busqueda semantica de codigo con ChromaDB + Embeddings.</p>' +
        '<div style="display: flex; gap: 10px; margin-bottom: 15px;">' +
            '<button onclick="getSemanticStatus()" style="flex: 1; padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">📊 Status</button>' +
            '<button onclick="indexWorkspace()" style="flex: 1; padding: 10px; background: #22c55e; color: white; border: none; border-radius: 6px; cursor: pointer;">🔄 Indexar</button>' +
            '<button onclick="getSemanticStats()" style="flex: 1; padding: 10px; background: #8b5cf6; color: white; border: none; border-radius: 6px; cursor: pointer;">📈 Stats</button>' +
        '</div>' +
        '<div style="margin-bottom: 15px;">' +
            '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">Buscar en codigo:</label>' +
            '<div style="display: flex; gap: 10px;">' +
                '<input type="text" id="semantic-query" placeholder="donde esta la autenticacion?" style="flex: 1; padding: 10px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb;">' +
                '<button onclick="semanticSearch()" style="padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">🔍 Buscar</button>' +
            '</div>' +
        '</div>' +
        '<div id="semantic-result" style="background: #0d1117; border-radius: 8px; padding: 15px; max-height: 350px; overflow-y: auto;">' +
            '<p style="color: #8b949e; text-align: center;">Usa los botones para indexar o buscar codigo</p>' +
        '</div>' +
    '</div>';
    showModal('Semantic Search', html);
}

async function getSemanticStatus() {
    var resultDiv = document.getElementById('semantic-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Obteniendo status...</p>';
    try {
        var response = await fetch('/api/semantic/status');
        var data = await response.json();
        
        var html = '<div style="padding: 10px;">' +
            '<h4 style="color: #3b82f6; margin: 0 0 15px 0;">📊 Semantic Search Status</h4>' +
            '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px;">' +
                '<div style="padding: 12px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 11px;">ChromaDB</div>' +
                    '<div style="font-size: 18px; color: ' + (data.chromadb_available ? '#22c55e' : '#ef4444') + '; font-weight: bold;">' + (data.chromadb_available ? '✓ OK' : '✗ NO') + '</div>' +
                '</div>' +
                '<div style="padding: 12px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 11px;">Transformers</div>' +
                    '<div style="font-size: 18px; color: ' + (data.sentence_transformers_available ? '#22c55e' : '#ef4444') + '; font-weight: bold;">' + (data.sentence_transformers_available ? '✓ OK' : '✗ NO') + '</div>' +
                '</div>' +
                '<div style="padding: 12px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 11px;">Workspaces</div>' +
                    '<div style="font-size: 18px; color: #f59e0b; font-weight: bold;">' + (data.active_workspaces || 0) + '</div>' +
                '</div>' +
                '<div style="padding: 12px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 11px;">Estado</div>' +
                    '<div style="font-size: 18px; color: #22c55e; font-weight: bold;">' + (data.status || 'active') + '</div>' +
                '</div>' +
            '</div>';
        
        if (data.features && data.features.length > 0) {
            html += '<div style="color: #8b949e; font-size: 12px;"><strong>Features:</strong><ul style="margin: 5px 0; padding-left: 20px;">';
            data.features.forEach(function(f) { html += '<li>' + f + '</li>'; });
            html += '</ul></div>';
        }
        html += '</div>';
        resultDiv.innerHTML = html;
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function indexWorkspace() {
    var resultDiv = document.getElementById('semantic-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Indexando workspace... (puede tomar varios segundos)</p>';
    try {
        var response = await fetch('/api/semantic/index', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace: '/workspace/project/test03', force: false })
        });
        var data = await response.json();
        
        if (data.success) {
            var stats = data.stats || {};
            var html = '<div style="padding: 10px;">' +
                '<h4 style="color: #22c55e; margin: 0 0 15px 0;">✅ Indexacion Completada</h4>' +
                '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">' +
                    '<div style="padding: 12px; background: #161b22; border-radius: 8px; text-align: center;">' +
                        '<div style="color: #8b949e; font-size: 11px;">Archivos</div>' +
                        '<div style="font-size: 24px; color: #3b82f6; font-weight: bold;">' + (stats.files_indexed || stats.files || 0) + '</div>' +
                    '</div>' +
                    '<div style="padding: 12px; background: #161b22; border-radius: 8px; text-align: center;">' +
                        '<div style="color: #8b949e; font-size: 11px;">Chunks</div>' +
                        '<div style="font-size: 24px; color: #22c55e; font-weight: bold;">' + (stats.chunks_created || stats.chunks || 0) + '</div>' +
                    '</div>' +
                    '<div style="padding: 12px; background: #161b22; border-radius: 8px; text-align: center;">' +
                        '<div style="color: #8b949e; font-size: 11px;">Tiempo</div>' +
                        '<div style="font-size: 24px; color: #f59e0b; font-weight: bold;">' + (stats.time || '0') + 's</div>' +
                    '</div>' +
                '</div>' +
            '</div>';
            resultDiv.innerHTML = html;
            showToast('Indexacion completada', 'success');
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || JSON.stringify(data)) + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function getSemanticStats() {
    var resultDiv = document.getElementById('semantic-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Obteniendo estadisticas...</p>';
    try {
        var response = await fetch('/api/semantic/stats?workspace=/workspace/project/test03');
        var data = await response.json();
        
        if (data.success) {
            var stats = data.stats || {};
            var html = '<div style="padding: 10px;">' +
                '<h4 style="color: #8b5cf6; margin: 0 0 15px 0;">📈 Estadisticas del Indice</h4>' +
                '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">' +
                    '<div style="padding: 12px; background: #161b22; border-radius: 8px;">' +
                        '<div style="color: #8b949e; font-size: 11px;">Total Documentos</div>' +
                        '<div style="font-size: 24px; color: #3b82f6; font-weight: bold;">' + (stats.total_documents || stats.documents || 0) + '</div>' +
                    '</div>' +
                    '<div style="padding: 12px; background: #161b22; border-radius: 8px;">' +
                        '<div style="color: #8b949e; font-size: 11px;">Chunks Indexados</div>' +
                        '<div style="font-size: 24px; color: #22c55e; font-weight: bold;">' + (stats.total_chunks || stats.chunks || 0) + '</div>' +
                    '</div>' +
                '</div>';
            
            if (stats.languages) {
                html += '<div style="margin-top: 15px;"><div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Lenguajes:</div>';
                Object.keys(stats.languages).forEach(function(lang) {
                    html += '<span style="display: inline-block; padding: 4px 8px; background: #1f2937; border-radius: 4px; margin: 2px; color: #e5e7eb; font-size: 11px;">' + lang + ': ' + stats.languages[lang] + '</span>';
                });
                html += '</div>';
            }
            html += '</div>';
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'No hay estadisticas') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function semanticSearch() {
    var query = document.getElementById('semantic-query').value;
    if (!query.trim()) { showToast('Ingresa una consulta', 'warning'); return; }
    
    var resultDiv = document.getElementById('semantic-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Buscando: "' + query + '"...</p>';
    
    try {
        var response = await fetch('/api/semantic/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace: '/workspace/project/test03', query: query, n_results: 10 })
        });
        var data = await response.json();
        
        if (data.success && data.results && data.results.length > 0) {
            var html = '<div style="padding: 10px;">' +
                '<h4 style="color: #3b82f6; margin: 0 0 10px 0;">🔍 Resultados para: "' + query + '"</h4>' +
                '<p style="color: #8b949e; font-size: 12px; margin-bottom: 15px;">Encontrados: ' + data.total + ' resultados</p>';
            
            data.results.forEach(function(r, idx) {
                var score = r.score || r.distance || 0;
                var scoreColor = score > 0.7 ? '#22c55e' : (score > 0.4 ? '#f59e0b' : '#ef4444');
                html += '<div style="margin-bottom: 10px; border: 1px solid #30363d; border-radius: 6px; overflow: hidden;">' +
                    '<div style="padding: 8px 10px; background: #161b22; display: flex; align-items: center; gap: 10px;">' +
                        '<span style="color: #6b7280; font-size: 11px;">#' + (idx + 1) + '</span>' +
                        '<span style="color: #e5e7eb; font-family: monospace; font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis;">' + (r.file || r.metadata?.file || 'unknown') + '</span>' +
                        '<span style="color: ' + scoreColor + '; font-size: 11px; font-weight: bold;">' + (score * 100).toFixed(0) + '%</span>' +
                    '</div>' +
                    '<pre style="margin: 0; padding: 10px; background: #0d1117; color: #c9d1d9; font-size: 11px; overflow-x: auto; max-height: 100px;">' + escapeHtmlSemantic(r.content || r.text || '') + '</pre>' +
                '</div>';
            });
            html += '</div>';
            resultDiv.innerHTML = html;
        } else if (data.results && data.results.length === 0) {
            resultDiv.innerHTML = '<p style="color: #f59e0b; text-align: center; padding: 20px;">No se encontraron resultados. Intenta indexar primero.</p>';
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || data.error || 'Error desconocido') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

function escapeHtmlSemantic(text) {
    if (!text) return '';
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// CODEMAPS FUNCTIONS - Grafo AST Interactivo
function openCodemaps() {
    var workspace = '/workspace/project/test03';
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Grafo de dependencias con analisis AST real.</p>' +
        '<div style="display: flex; gap: 10px; margin-bottom: 15px;">' +
            '<button onclick="getCodemapStatus()" style="flex: 1; padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">📊 Status</button>' +
            '<button onclick="scanCodemap()" style="flex: 1; padding: 10px; background: #f59e0b; color: white; border: none; border-radius: 6px; cursor: pointer;">🔍 Escanear</button>' +
        '</div>' +
        '<div id="codemap-result" style="background: #0d1117; border-radius: 8px; padding: 15px; min-height: 300px; max-height: 450px; overflow: auto;">' +
            '<p style="color: #8b949e; text-align: center;">Haz clic en Escanear para generar el grafo de dependencias</p>' +
        '</div>' +
    '</div>';
    showModal('Codemaps - Grafo AST', html);
}

async function getCodemapStatus() {
    var resultDiv = document.getElementById('codemap-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Obteniendo status...</p>';
    try {
        var response = await fetch('/api/codemap/status');
        var data = await response.json();
        
        var html = '<div style="padding: 10px;">' +
            '<h4 style="color: #f59e0b; margin: 0 0 15px 0;">📊 Codemap Status</h4>' +
            '<div style="padding: 12px; background: #161b22; border-radius: 8px; margin-bottom: 15px;">' +
                '<div style="color: #8b949e; font-size: 11px;">Estado</div>' +
                '<div style="font-size: 18px; color: #22c55e; font-weight: bold;">' + (data.status || 'active') + '</div>' +
            '</div>';
        
        if (data.features) {
            html += '<div style="margin-bottom: 15px;"><div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Features:</div><ul style="margin: 0; padding-left: 20px; color: #c9d1d9; font-size: 12px;">';
            data.features.forEach(function(f) { html += '<li>' + f + '</li>'; });
            html += '</ul></div>';
        }
        
        if (data.supported_extensions) {
            html += '<div><div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Extensiones soportadas:</div>';
            data.supported_extensions.forEach(function(ext) {
                html += '<span style="display: inline-block; padding: 4px 8px; background: #1f2937; border-radius: 4px; margin: 2px; color: #f59e0b; font-size: 11px;">' + ext + '</span>';
            });
            html += '</div>';
        }
        html += '</div>';
        resultDiv.innerHTML = html;
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function scanCodemap() {
    var resultDiv = document.getElementById('codemap-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Escaneando workspace y analizando AST... (puede tomar varios segundos)</p>';
    
    try {
        var response = await fetch('/api/codemap/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace: '/workspace/project/test03', max_files: 100 })
        });
        var data = await response.json();
        
        if (data.success && data.graph) {
            renderCodemap(data.graph, data.stats);
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.error || 'No se pudo generar el grafo') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

function renderCodemap(graph, stats) {
    var resultDiv = document.getElementById('codemap-result');
    var nodes = graph.nodes || [];
    var edges = graph.edges || [];
    
    var html = '<div style="padding: 10px;">' +
        '<h4 style="color: #f59e0b; margin: 0 0 15px 0;">🗺️ Grafo de Dependencias</h4>' +
        '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 15px;">' +
            '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                '<div style="color: #8b949e; font-size: 10px;">Archivos</div>' +
                '<div style="font-size: 20px; color: #3b82f6; font-weight: bold;">' + (stats.files || nodes.length) + '</div>' +
            '</div>' +
            '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                '<div style="color: #8b949e; font-size: 10px;">Dependencias</div>' +
                '<div style="font-size: 20px; color: #f59e0b; font-weight: bold;">' + edges.length + '</div>' +
            '</div>' +
            '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                '<div style="color: #8b949e; font-size: 10px;">Funciones</div>' +
                '<div style="font-size: 20px; color: #22c55e; font-weight: bold;">' + (stats.functions || 0) + '</div>' +
            '</div>' +
            '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                '<div style="color: #8b949e; font-size: 10px;">Clases</div>' +
                '<div style="font-size: 20px; color: #8b5cf6; font-weight: bold;">' + (stats.classes || 0) + '</div>' +
            '</div>' +
        '</div>';
    
    // Mostrar nodos por tipo
    var nodesByType = {};
    nodes.forEach(function(n) {
        var type = n.type || 'file';
        if (!nodesByType[type]) nodesByType[type] = [];
        nodesByType[type].push(n);
    });
    
    var typeColors = { 'file': '#3b82f6', 'function': '#22c55e', 'class': '#8b5cf6', 'import': '#f59e0b' };
    var typeIcons = { 'file': '📄', 'function': '⚡', 'class': '🔷', 'import': '📦' };
    
    Object.keys(nodesByType).forEach(function(type) {
        var items = nodesByType[type];
        if (items.length === 0) return;
        
        html += '<div style="margin-bottom: 15px;">' +
            '<div style="color: ' + (typeColors[type] || '#8b949e') + '; font-size: 12px; margin-bottom: 8px; font-weight: bold;">' + 
            (typeIcons[type] || '•') + ' ' + type.toUpperCase() + ' (' + items.length + ')</div>' +
            '<div style="display: flex; flex-wrap: wrap; gap: 5px;">';
        
        items.slice(0, 20).forEach(function(item) {
            var name = item.name || item.id || 'unknown';
            if (name.length > 30) name = name.substring(0, 27) + '...';
            html += '<span style="padding: 4px 8px; background: #1f2937; border-radius: 4px; color: #c9d1d9; font-size: 11px; font-family: monospace; border-left: 3px solid ' + (typeColors[type] || '#6b7280') + ';">' + name + '</span>';
        });
        
        if (items.length > 20) {
            html += '<span style="padding: 4px 8px; color: #8b949e; font-size: 11px;">+' + (items.length - 20) + ' mas</span>';
        }
        html += '</div></div>';
    });
    
    // Mostrar algunas dependencias
    if (edges.length > 0) {
        html += '<div style="margin-top: 15px;">' +
            '<div style="color: #f59e0b; font-size: 12px; margin-bottom: 8px; font-weight: bold;">🔗 DEPENDENCIAS (primeras 10)</div>' +
            '<div style="font-family: monospace; font-size: 11px;">';
        
        edges.slice(0, 10).forEach(function(edge) {
            var from = edge.source || edge.from || '?';
            var to = edge.target || edge.to || '?';
            if (from.length > 25) from = from.substring(0, 22) + '...';
            if (to.length > 25) to = to.substring(0, 22) + '...';
            html += '<div style="padding: 4px 8px; background: #161b22; margin: 2px 0; border-radius: 4px;">' +
                '<span style="color: #3b82f6;">' + from + '</span>' +
                '<span style="color: #6b7280;"> → </span>' +
                '<span style="color: #22c55e;">' + to + '</span>' +
            '</div>';
        });
        
        if (edges.length > 10) {
            html += '<div style="color: #8b949e; padding: 4px;">... y ' + (edges.length - 10) + ' dependencias mas</div>';
        }
        html += '</div></div>';
    }
    
    html += '</div>';
    resultDiv.innerHTML = html;
    showToast('Grafo generado: ' + nodes.length + ' nodos, ' + edges.length + ' dependencias', 'success');
}

// CHECKPOINTS FUNCTIONS - Git Snapshots Reales
function openCheckpoints() {
    var workspace = '/workspace/project/test03';
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Sistema de snapshots Git reales para tu proyecto.</p>' +
        '<div style="display: flex; gap: 10px; margin-bottom: 15px;">' +
            '<button onclick="listCheckpoints()" style="flex: 1; padding: 10px; background: #06b6d4; color: white; border: none; border-radius: 6px; cursor: pointer;">📋 Listar</button>' +
            '<button onclick="showCreateCheckpoint()" style="flex: 1; padding: 10px; background: #22c55e; color: white; border: none; border-radius: 6px; cursor: pointer;">➕ Crear</button>' +
        '</div>' +
        '<div id="checkpoint-result" style="background: #0d1117; border-radius: 8px; padding: 15px; min-height: 300px; max-height: 450px; overflow: auto;">' +
            '<p style="color: #8b949e; text-align: center;">Haz clic en Listar para ver checkpoints o Crear para nuevo snapshot</p>' +
        '</div>' +
    '</div>';
    showModal('Checkpoints - Git Snapshots', html);
}

async function listCheckpoints() {
    var resultDiv = document.getElementById('checkpoint-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Cargando checkpoints...</p>';
    
    try {
        var response = await fetch('/api/checkpoints/list?limit=20');
        var data = await response.json();
        
        if (data.success) {
            var checkpoints = data.checkpoints || [];
            var stats = data.stats || {};
            
            var html = '<div style="padding: 10px;">' +
                '<h4 style="color: #06b6d4; margin: 0 0 15px 0;">📋 Checkpoints Disponibles</h4>' +
                '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 15px;">' +
                    '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                        '<div style="color: #8b949e; font-size: 10px;">Total</div>' +
                        '<div style="font-size: 20px; color: #06b6d4; font-weight: bold;">' + (stats.total_checkpoints || 0) + '</div>' +
                    '</div>' +
                    '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                        '<div style="color: #8b949e; font-size: 10px;">Archivos</div>' +
                        '<div style="font-size: 20px; color: #22c55e; font-weight: bold;">' + (stats.total_files_stored || 0) + '</div>' +
                    '</div>' +
                    '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                        '<div style="color: #8b949e; font-size: 10px;">Tamaño</div>' +
                        '<div style="font-size: 20px; color: #f59e0b; font-weight: bold;">' + (stats.total_size_mb || 0).toFixed(2) + ' MB</div>' +
                    '</div>' +
                '</div>';
            
            if (checkpoints.length === 0) {
                html += '<p style="color: #8b949e; text-align: center; padding: 20px;">No hay checkpoints creados. Haz clic en "Crear" para crear uno.</p>';
            } else {
                html += '<div style="border: 1px solid #30363d; border-radius: 8px; overflow: hidden;">';
                checkpoints.forEach(function(cp, idx) {
                    html += '<div style="padding: 12px; border-bottom: 1px solid #30363d; background: ' + (idx % 2 === 0 ? '#161b22' : '#0d1117') + ';">' +
                        '<div style="display: flex; justify-content: space-between; align-items: center;">' +
                            '<div>' +
                                '<div style="color: #e5e7eb; font-weight: bold;">📸 ' + (cp.name || cp.id) + '</div>' +
                                '<div style="color: #8b949e; font-size: 11px;">' + (cp.description || 'Sin descripcion') + '</div>' +
                                '<div style="color: #6b7280; font-size: 10px;">' + (cp.created_at || '') + ' • ' + (cp.file_count || 0) + ' archivos</div>' +
                            '</div>' +
                            '<div style="display: flex; gap: 5px;">' +
                                '<button onclick="previewCheckpoint(\'' + cp.id + '\')" style="padding: 5px 10px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">👁️</button>' +
                                '<button onclick="restoreCheckpoint(\'' + cp.id + '\')" style="padding: 5px 10px; background: #f59e0b; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">↩️</button>' +
                            '</div>' +
                        '</div>' +
                    '</div>';
                });
                html += '</div>';
            }
            html += '</div>';
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'Error desconocido') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

function showCreateCheckpoint() {
    var resultDiv = document.getElementById('checkpoint-result');
    var html = '<div style="padding: 10px;">' +
        '<h4 style="color: #22c55e; margin: 0 0 15px 0;">➕ Crear Nuevo Checkpoint</h4>' +
        '<div style="margin-bottom: 15px;">' +
            '<label style="display: block; color: #8b949e; font-size: 12px; margin-bottom: 5px;">Nombre del checkpoint:</label>' +
            '<input type="text" id="checkpoint-name" placeholder="v1.0-feature-login" style="width: 100%; padding: 10px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; color: #e5e7eb;">' +
        '</div>' +
        '<div style="margin-bottom: 15px;">' +
            '<label style="display: block; color: #8b949e; font-size: 12px; margin-bottom: 5px;">Descripcion (opcional):</label>' +
            '<textarea id="checkpoint-desc" placeholder="Descripcion del estado actual..." style="width: 100%; padding: 10px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; color: #e5e7eb; min-height: 60px; resize: vertical;"></textarea>' +
        '</div>' +
        '<button onclick="createCheckpoint()" style="width: 100%; padding: 12px; background: #22c55e; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">📸 Crear Snapshot</button>' +
    '</div>';
    resultDiv.innerHTML = html;
}

async function createCheckpoint() {
    var name = document.getElementById('checkpoint-name').value;
    var desc = document.getElementById('checkpoint-desc').value;
    
    if (!name.trim()) {
        showToast('Ingresa un nombre para el checkpoint', 'warning');
        return;
    }
    
    var resultDiv = document.getElementById('checkpoint-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Creando checkpoint... (escaneando archivos)</p>';
    
    try {
        var response = await fetch('/api/checkpoints/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                workspace: '/workspace/project/test03',
                name: name,
                description: desc
            })
        });
        var data = await response.json();
        
        if (data.success) {
            var cp = data.checkpoint || {};
            var html = '<div style="padding: 10px;">' +
                '<h4 style="color: #22c55e; margin: 0 0 15px 0;">✅ Checkpoint Creado</h4>' +
                '<div style="padding: 15px; background: #161b22; border-radius: 8px; border-left: 4px solid #22c55e;">' +
                    '<div style="color: #e5e7eb; font-weight: bold; font-size: 16px;">📸 ' + cp.name + '</div>' +
                    '<div style="color: #8b949e; margin: 5px 0;">' + (cp.description || 'Sin descripcion') + '</div>' +
                    '<div style="display: flex; gap: 15px; margin-top: 10px;">' +
                        '<span style="color: #06b6d4;">📄 ' + cp.file_count + ' archivos</span>' +
                        '<span style="color: #f59e0b;">💾 ' + ((cp.total_size || 0) / 1024).toFixed(1) + ' KB</span>' +
                        '<span style="color: #8b949e;">🕐 ' + (cp.created_at || 'ahora') + '</span>' +
                    '</div>' +
                '</div>' +
                '<button onclick="listCheckpoints()" style="width: 100%; margin-top: 15px; padding: 10px; background: #06b6d4; color: white; border: none; border-radius: 6px; cursor: pointer;">📋 Ver Todos los Checkpoints</button>' +
            '</div>';
            resultDiv.innerHTML = html;
            showToast('Checkpoint creado: ' + cp.file_count + ' archivos', 'success');
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'Error al crear checkpoint') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function previewCheckpoint(checkpointId) {
    var resultDiv = document.getElementById('checkpoint-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Cargando preview...</p>';
    
    try {
        var response = await fetch('/api/checkpoints/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ checkpoint_id: checkpointId, dry_run: true })
        });
        var data = await response.json();
        
        if (data.success) {
            var result = data.result || {};
            var html = '<div style="padding: 10px;">' +
                '<h4 style="color: #3b82f6; margin: 0 0 15px 0;">👁️ Preview del Checkpoint</h4>' +
                '<div style="padding: 15px; background: #161b22; border-radius: 8px;">' +
                    '<p style="color: #8b949e; font-size: 12px;">Cambios que se aplicarian:</p>' +
                    '<div style="display: flex; gap: 10px; margin: 10px 0;">' +
                        '<span style="padding: 5px 10px; background: #22c55e20; color: #22c55e; border-radius: 4px;">+ ' + (result.files_to_create || 0) + ' crear</span>' +
                        '<span style="padding: 5px 10px; background: #f59e0b20; color: #f59e0b; border-radius: 4px;">~ ' + (result.files_to_modify || 0) + ' modificar</span>' +
                        '<span style="padding: 5px 10px; background: #ef444420; color: #ef4444; border-radius: 4px;">- ' + (result.files_to_delete || 0) + ' eliminar</span>' +
                    '</div>' +
                '</div>' +
                '<button onclick="listCheckpoints()" style="width: 100%; margin-top: 15px; padding: 10px; background: #06b6d4; color: white; border: none; border-radius: 6px; cursor: pointer;">← Volver</button>' +
            '</div>';
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'Error al cargar preview') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function restoreCheckpoint(checkpointId) {
    if (!confirm('¿Restaurar este checkpoint? Los archivos actuales seran reemplazados.')) return;
    
    var resultDiv = document.getElementById('checkpoint-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Restaurando checkpoint...</p>';
    
    try {
        var response = await fetch('/api/checkpoints/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ checkpoint_id: checkpointId, dry_run: false })
        });
        var data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = '<div style="padding: 20px; text-align: center;">' +
                '<div style="font-size: 48px; margin-bottom: 15px;">✅</div>' +
                '<h4 style="color: #22c55e;">Checkpoint Restaurado</h4>' +
                '<p style="color: #8b949e;">El proyecto ha sido restaurado al estado del checkpoint.</p>' +
                '<button onclick="listCheckpoints()" style="margin-top: 15px; padding: 10px 20px; background: #06b6d4; color: white; border: none; border-radius: 6px; cursor: pointer;">📋 Ver Checkpoints</button>' +
            '</div>';
            showToast('Checkpoint restaurado correctamente', 'success');
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'Error al restaurar') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

// BACKGROUND AGENTS FUNCTIONS - Ejecución Paralela Real
function openBackgroundAgents() {
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Ejecuta tareas en paralelo con workers reales.</p>' +
        '<div style="display: flex; gap: 10px; margin-bottom: 15px;">' +
            '<button onclick="getBackgroundStatus()" style="flex: 1; padding: 10px; background: #eab308; color: black; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">📊 Status</button>' +
            '<button onclick="listBackgroundTasks()" style="flex: 1; padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">📋 Tareas</button>' +
        '</div>' +
        '<div style="margin-bottom: 15px; padding: 10px; background: #161b22; border-radius: 8px;">' +
            '<div style="color: #8b949e; font-size: 11px; margin-bottom: 8px;">Ejecutar tarea de prueba:</div>' +
            '<div style="display: flex; gap: 8px; flex-wrap: wrap;">' +
                '<button onclick="submitBackgroundTask(\'slow\', {seconds: 5, name: \'Test Slow\'})" style="padding: 8px 12px; background: #6366f1; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">⏳ Slow (5s)</button>' +
                '<button onclick="submitBackgroundTask(\'compute\', {n: 5000000})" style="padding: 8px 12px; background: #22c55e; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">🔢 Compute</button>' +
                '<button onclick="submitBackgroundTask(\'analyze\', {code: \'def hello(): return 42\'})" style="padding: 8px 12px; background: #f59e0b; color: black; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">📝 Analyze</button>' +
            '</div>' +
        '</div>' +
        '<div id="background-result" style="background: #0d1117; border-radius: 8px; padding: 15px; min-height: 280px; max-height: 400px; overflow: auto;">' +
            '<p style="color: #8b949e; text-align: center;">Haz clic en Status para ver los workers o ejecuta una tarea</p>' +
        '</div>' +
    '</div>';
    showModal('Background Agents', html);
}

async function getBackgroundStatus() {
    var resultDiv = document.getElementById('background-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Obteniendo status...</p>';
    
    try {
        var response = await fetch('/api/background/status');
        var data = await response.json();
        
        var html = '<div style="padding: 10px;">' +
            '<h4 style="color: #eab308; margin: 0 0 15px 0;">📊 Background Agents Status</h4>' +
            '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 15px;">' +
                '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 10px;">Workers Total</div>' +
                    '<div style="font-size: 20px; color: #3b82f6; font-weight: bold;">' + (data.workers_total || 0) + '</div>' +
                '</div>' +
                '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 10px;">Ocupados</div>' +
                    '<div style="font-size: 20px; color: #f59e0b; font-weight: bold;">' + (data.workers_busy || 0) + '</div>' +
                '</div>' +
                '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 10px;">Libres</div>' +
                    '<div style="font-size: 20px; color: #22c55e; font-weight: bold;">' + (data.workers_idle || 0) + '</div>' +
                '</div>' +
                '<div style="padding: 10px; background: #161b22; border-radius: 8px; text-align: center;">' +
                    '<div style="color: #8b949e; font-size: 10px;">En Cola</div>' +
                    '<div style="font-size: 20px; color: #8b5cf6; font-weight: bold;">' + (data.queue_size || 0) + '</div>' +
                '</div>' +
            '</div>';
        
        var tasks = data.tasks || {};
        html += '<div style="margin-bottom: 15px;">' +
            '<div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Tareas:</div>' +
            '<div style="display: flex; gap: 10px; flex-wrap: wrap;">' +
                '<span style="padding: 5px 10px; background: #1f2937; border-radius: 4px; color: #8b949e;">Total: ' + (tasks.total || 0) + '</span>' +
                '<span style="padding: 5px 10px; background: #fef3c720; border-radius: 4px; color: #fef08a;">⏳ Pending: ' + (tasks.pending || 0) + '</span>' +
                '<span style="padding: 5px 10px; background: #3b82f620; border-radius: 4px; color: #60a5fa;">🔄 Running: ' + (tasks.running || 0) + '</span>' +
                '<span style="padding: 5px 10px; background: #22c55e20; border-radius: 4px; color: #4ade80;">✅ Completed: ' + (tasks.completed || 0) + '</span>' +
                '<span style="padding: 5px 10px; background: #ef444420; border-radius: 4px; color: #f87171;">❌ Failed: ' + (tasks.failed || 0) + '</span>' +
            '</div>' +
        '</div>';
        
        if (data.features && data.features.length > 0) {
            html += '<div style="color: #8b949e; font-size: 11px;"><strong>Features:</strong><ul style="margin: 5px 0; padding-left: 20px;">';
            data.features.forEach(function(f) { html += '<li>' + f + '</li>'; });
            html += '</ul></div>';
        }
        html += '</div>';
        resultDiv.innerHTML = html;
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function submitBackgroundTask(taskType, params) {
    var resultDiv = document.getElementById('background-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Enviando tarea...</p>';
    
    try {
        var response = await fetch('/api/background/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_type: taskType, params: params, priority: 'NORMAL' })
        });
        var data = await response.json();
        
        if (data.success) {
            showToast('Tarea enviada: ' + data.task_id, 'success');
            // Mostrar confirmación y luego actualizar status
            var html = '<div style="padding: 20px; text-align: center;">' +
                '<div style="font-size: 48px; margin-bottom: 15px;">✅</div>' +
                '<h4 style="color: #22c55e;">Tarea Enviada</h4>' +
                '<p style="color: #8b949e;">ID: <code style="background: #1f2937; padding: 2px 6px; border-radius: 4px;">' + data.task_id + '</code></p>' +
                '<p style="color: #6b7280; font-size: 12px;">' + data.message + '</p>' +
            '</div>';
            resultDiv.innerHTML = html;
            
            // Auto-actualizar después de un momento
            setTimeout(function() { listBackgroundTasks(); }, 1000);
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'Error desconocido') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

async function listBackgroundTasks() {
    var resultDiv = document.getElementById('background-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Cargando tareas...</p>';
    
    try {
        var response = await fetch('/api/background/tasks?limit=20');
        var data = await response.json();
        
        if (data.success) {
            var tasks = data.tasks || [];
            var html = '<div style="padding: 10px;">' +
                '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">' +
                    '<h4 style="color: #3b82f6; margin: 0;">📋 Tareas (' + tasks.length + ')</h4>' +
                    '<button onclick="listBackgroundTasks()" style="padding: 5px 10px; background: #1f2937; color: #8b949e; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">🔄 Refresh</button>' +
                '</div>';
            
            if (tasks.length === 0) {
                html += '<p style="color: #8b949e; text-align: center; padding: 20px;">No hay tareas. Ejecuta una tarea de prueba.</p>';
            } else {
                html += '<div style="border: 1px solid #30363d; border-radius: 8px; overflow: hidden;">';
                tasks.forEach(function(task, idx) {
                    var statusColor = task.status === 'completed' ? '#22c55e' : (task.status === 'running' ? '#3b82f6' : (task.status === 'failed' ? '#ef4444' : '#f59e0b'));
                    var statusIcon = task.status === 'completed' ? '✅' : (task.status === 'running' ? '🔄' : (task.status === 'failed' ? '❌' : '⏳'));
                    
                    html += '<div style="padding: 10px; border-bottom: 1px solid #30363d; background: ' + (idx % 2 === 0 ? '#161b22' : '#0d1117') + ';">' +
                        '<div style="display: flex; justify-content: space-between; align-items: center;">' +
                            '<div>' +
                                '<div style="color: #e5e7eb; font-weight: bold;">' + (task.name || task.id) + '</div>' +
                                '<div style="color: #6b7280; font-size: 10px;">' + (task.created_at || '') + '</div>' +
                            '</div>' +
                            '<div style="display: flex; align-items: center; gap: 8px;">' +
                                '<span style="padding: 3px 8px; background: ' + statusColor + '20; color: ' + statusColor + '; border-radius: 4px; font-size: 11px;">' + statusIcon + ' ' + (task.status || 'unknown') + '</span>';
                    
                    if (task.result && task.status === 'completed') {
                        html += '<span style="color: #8b949e; font-size: 10px;">Result: ' + JSON.stringify(task.result).substring(0, 30) + '...</span>';
                    }
                    html += '</div></div></div>';
                });
                html += '</div>';
            }
            html += '</div>';
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'Error desconocido') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

// AUTO-FIX LOOP FUNCTIONS - Detectar→Corregir→Re-ejecutar
function openAutoFix() {
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Loop automatico: detectar errores → corregir → re-ejecutar → verificar.</p>' +
        '<div style="margin-bottom: 15px;">' +
            '<label style="display: block; color: #8b949e; font-size: 12px; margin-bottom: 5px;">Codigo a corregir:</label>' +
            '<textarea id="autofix-code" placeholder="print(1/0)&#10;# o cualquier codigo con errores" style="width: 100%; height: 120px; padding: 10px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; color: #e5e7eb; font-family: monospace; font-size: 12px; resize: vertical;"></textarea>' +
        '</div>' +
        '<div style="display: flex; gap: 10px; margin-bottom: 15px;">' +
            '<select id="autofix-lang" style="padding: 10px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; color: #e5e7eb;">' +
                '<option value="python">Python</option>' +
                '<option value="javascript">JavaScript</option>' +
            '</select>' +
            '<input type="number" id="autofix-iterations" value="5" min="1" max="10" style="width: 80px; padding: 10px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; color: #e5e7eb;" title="Max iteraciones">' +
            '<button onclick="runAutoFix()" style="flex: 1; padding: 10px; background: #f97316; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">🔄 Ejecutar Auto-Fix Loop</button>' +
        '</div>' +
        '<div id="autofix-result" style="background: #0d1117; border-radius: 8px; padding: 15px; min-height: 250px; max-height: 400px; overflow: auto;">' +
            '<p style="color: #8b949e; text-align: center;">Ingresa codigo con errores y ejecuta el loop de auto-fix</p>' +
        '</div>' +
    '</div>';
    showModal('Auto-Fix Loop', html);
}

async function runAutoFix() {
    var code = document.getElementById('autofix-code').value;
    var lang = document.getElementById('autofix-lang').value;
    var maxIter = parseInt(document.getElementById('autofix-iterations').value) || 5;
    
    if (!code.trim()) {
        showToast('Ingresa codigo para corregir', 'warning');
        return;
    }
    
    var resultDiv = document.getElementById('autofix-result');
    resultDiv.innerHTML = '<p style="color: #8b949e;">⏳ Ejecutando loop de auto-fix...</p>' +
        '<div style="margin-top: 10px;">' +
            '<div style="color: #6b7280; font-size: 11px;">Loop: detectar → corregir → re-ejecutar → verificar</div>' +
            '<div style="margin-top: 5px; height: 4px; background: #1f2937; border-radius: 2px; overflow: hidden;">' +
                '<div style="width: 30%; height: 100%; background: #f97316; animation: pulse 1s infinite;"></div>' +
            '</div>' +
        '</div>';
    
    try {
        var response = await fetch('/api/autofix/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: lang,
                max_iterations: maxIter,
                apply_fixes: true,
                verify_fixes: true
            })
        });
        var data = await response.json();
        
        if (data.success !== undefined) {
            renderAutoFixResult(data);
        } else {
            resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + (data.detail || 'Error desconocido') + '</p>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}

function renderAutoFixResult(data) {
    var resultDiv = document.getElementById('autofix-result');
    var statusColor = data.success ? '#22c55e' : '#ef4444';
    var statusIcon = data.success ? '✅' : '❌';
    
    var html = '<div style="padding: 10px;">' +
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">' +
            '<h4 style="color: #f97316; margin: 0;">🔄 Auto-Fix Resultado</h4>' +
            '<span style="padding: 5px 10px; background: ' + statusColor + '20; color: ' + statusColor + '; border-radius: 4px; font-size: 12px;">' + statusIcon + ' ' + (data.status || 'unknown') + '</span>' +
        '</div>' +
        '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 15px;">' +
            '<div style="padding: 8px; background: #161b22; border-radius: 6px; text-align: center;">' +
                '<div style="color: #8b949e; font-size: 10px;">Iteraciones</div>' +
                '<div style="font-size: 18px; color: #3b82f6; font-weight: bold;">' + (data.iterations_count || 0) + '</div>' +
            '</div>' +
            '<div style="padding: 8px; background: #161b22; border-radius: 6px; text-align: center;">' +
                '<div style="color: #8b949e; font-size: 10px;">Fixes</div>' +
                '<div style="font-size: 18px; color: #22c55e; font-weight: bold;">' + (data.total_fixes_applied || 0) + '</div>' +
            '</div>' +
            '<div style="padding: 8px; background: #161b22; border-radius: 6px; text-align: center;">' +
                '<div style="color: #8b949e; font-size: 10px;">Tiempo</div>' +
                '<div style="font-size: 18px; color: #f59e0b; font-weight: bold;">' + (data.total_time || 0).toFixed(2) + 's</div>' +
            '</div>' +
            '<div style="padding: 8px; background: #161b22; border-radius: 6px; text-align: center;">' +
                '<div style="color: #8b949e; font-size: 10px;">Verificado</div>' +
                '<div style="font-size: 18px; color: ' + (data.verified ? '#22c55e' : '#ef4444') + '; font-weight: bold;">' + (data.verified ? '✓' : '✗') + '</div>' +
            '</div>' +
        '</div>';
    
    // Mostrar iteraciones del loop
    if (data.iterations && data.iterations.length > 0) {
        html += '<div style="margin-bottom: 15px;">' +
            '<div style="color: #8b949e; font-size: 12px; margin-bottom: 8px; font-weight: bold;">📊 Loop de Iteraciones:</div>' +
            '<div style="border: 1px solid #30363d; border-radius: 6px; overflow: hidden;">';
        
        data.iterations.forEach(function(iter, idx) {
            var iterColor = iter.status === 'success' ? '#22c55e' : (iter.status === 'fixing' ? '#f59e0b' : '#3b82f6');
            var iterIcon = iter.status === 'success' ? '✅' : (iter.status === 'fixing' ? '🔧' : '🔍');
            
            html += '<div style="padding: 8px 10px; border-bottom: 1px solid #30363d; background: ' + (idx % 2 === 0 ? '#161b22' : '#0d1117') + ';">' +
                '<div style="display: flex; justify-content: space-between; align-items: center;">' +
                    '<div>' +
                        '<span style="color: #6b7280; font-size: 11px;">Iteracion ' + (idx + 1) + '</span>' +
                        '<span style="color: ' + iterColor + '; margin-left: 10px; font-size: 11px;">' + iterIcon + ' ' + (iter.status || '') + '</span>' +
                    '</div>' +
                    '<div style="color: #8b949e; font-size: 10px;">' + (iter.fix_description || '') + '</div>' +
                '</div>' +
            '</div>';
        });
        html += '</div></div>';
    }
    
    // Mostrar codigo original vs final
    if (data.code_changed) {
        html += '<div style="margin-bottom: 15px;">' +
            '<div style="color: #ef4444; font-size: 11px; margin-bottom: 5px;">❌ Codigo Original (con error):</div>' +
            '<pre style="margin: 0; padding: 8px; background: #1c1c1c; border-radius: 4px; color: #f87171; font-size: 11px; overflow-x: auto; border-left: 3px solid #ef4444;">' + escapeHtmlAutoFix(data.original_code) + '</pre>' +
        '</div>' +
        '<div style="margin-bottom: 15px;">' +
            '<div style="color: #22c55e; font-size: 11px; margin-bottom: 5px;">✅ Codigo Corregido:</div>' +
            '<pre style="margin: 0; padding: 8px; background: #1c1c1c; border-radius: 4px; color: #4ade80; font-size: 11px; overflow-x: auto; border-left: 3px solid #22c55e;">' + escapeHtmlAutoFix(data.final_code) + '</pre>' +
        '</div>';
    }
    
    // Mostrar output final
    if (data.final_output) {
        html += '<div>' +
            '<div style="color: #3b82f6; font-size: 11px; margin-bottom: 5px;">📤 Output Final:</div>' +
            '<pre style="margin: 0; padding: 8px; background: #0a0a0a; border-radius: 4px; color: #60a5fa; font-size: 11px; overflow-x: auto;">' + escapeHtmlAutoFix(data.final_output) + '</pre>' +
        '</div>';
    }
    
    if (data.error_message) {
        html += '<div style="margin-top: 10px; padding: 8px; background: #ef444420; border-radius: 4px; color: #f87171; font-size: 11px;">' +
            '⚠️ ' + data.error_message +
        '</div>';
    }
    
    html += '</div>';
    resultDiv.innerHTML = html;
    
    if (data.success) {
        showToast('Auto-Fix completado: ' + data.total_fixes_applied + ' correcciones aplicadas', 'success');
    }
}

function escapeHtmlAutoFix(text) {
    if (!text) return '';
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// MCTS OPTIMIZER - Actualizado para usar Monte Carlo real
function openMCTSOptimizer() {
    var html = '<div style="padding: 20px;">' +
        '<p style="margin-bottom: 15px; color: #9ca3af;">Monte Carlo Tree Search con evaluacion real para optimizacion.</p>' +
        '<div style="margin-bottom: 15px;">' +
            '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">Expresion a optimizar:</label>' +
            '<input type="text" id="mcts-expression" value="x**2 + y**2" placeholder="x**2 + y**2" style="width: 100%; padding: 10px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb; font-family: monospace;">' +
        '</div>' +
        '<div style="margin-bottom: 15px;">' +
            '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">Rango de parametros (JSON):</label>' +
            '<textarea id="mcts-params" style="width: 100%; height: 80px; padding: 10px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb; font-family: monospace;">{"x": [-10, 10], "y": [-10, 10]}</textarea>' +
        '</div>' +
        '<div style="margin-bottom: 15px; display: flex; gap: 15px;">' +
            '<div style="flex: 1;">' +
                '<label style="display: block; margin-bottom: 5px; color: #9ca3af;">Simulaciones:</label>' +
                '<input type="number" id="mcts-simulations" value="1000" style="width: 100%; padding: 8px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb;">' +
            '</div>' +
            '<div style="flex: 1;">' +
                '<label style="display: block; margin-bottom: 5px; color: #9ca3af;">Objetivo:</label>' +
                '<select id="mcts-objective" style="width: 100%; padding: 8px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb;">' +
                    '<option value="minimize">Minimizar</option>' +
                    '<option value="maximize">Maximizar</option>' +
                '</select>' +
            '</div>' +
        '</div>' +
        '<button onclick="executeMCTSReal()" style="padding: 10px 20px; background: #14b8a6; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">🎯 Ejecutar MCTS</button>' +
        '<div id="mcts-result" style="margin-top: 15px; background: #0d1117; padding: 15px; border-radius: 8px; min-height: 200px; display: none;">' +
            '<div id="mcts-output" style="color: #e5e7eb;"></div>' +
        '</div>' +
    '</div>';
    showModal('MCTS Optimizer', html);
}

async function executeMCTSReal() {
    var expression = document.getElementById('mcts-expression').value;
    var paramsText = document.getElementById('mcts-params').value;
    var simulations = parseInt(document.getElementById('mcts-simulations').value) || 1000;
    var objective = document.getElementById('mcts-objective').value;

    if (!expression) { showToast('Ingresa una expresion', 'warning'); return; }

    var params;
    try {
        params = JSON.parse(paramsText);
    } catch(e) {
        showToast('JSON de parametros invalido', 'error');
        return;
    }

    var resultDiv = document.getElementById('mcts-result');
    var outputDiv = document.getElementById('mcts-output');
    resultDiv.style.display = 'block';
    outputDiv.innerHTML = '<p style="color: #9ca3af;">⏳ Ejecutando Monte Carlo (' + simulations + ' simulaciones)...</p>';

    try {
        var response = await fetch('/api/advanced/ml/monte-carlo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                expression: expression,
                params_ranges: params,
                n_simulations: simulations,
                objective: objective
            })
        });
        var data = await response.json();

        if (data.results) {
            var r = data.results;
            var stats = data.statistics || {};
            
            var html = '<div style="padding: 10px;">' +
                '<h4 style="color: #14b8a6; margin: 0 0 15px 0;">🎯 MCTS Completado</h4>' +
                '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">' +
                    '<div style="padding: 15px; background: #161b22; border-radius: 8px; text-align: center; border: 1px solid #14b8a6;">' +
                        '<div style="color: #8b949e; font-size: 11px; margin-bottom: 5px;">Mejor Valor</div>' +
                        '<div style="font-size: 24px; color: #14b8a6; font-weight: bold;">' + (r.best_value || 0).toFixed(6) + '</div>' +
                    '</div>' +
                    '<div style="padding: 15px; background: #161b22; border-radius: 8px; text-align: center;">' +
                        '<div style="color: #8b949e; font-size: 11px; margin-bottom: 5px;">Simulaciones</div>' +
                        '<div style="font-size: 24px; color: #3b82f6; font-weight: bold;">' + (r.samples_evaluated || simulations) + '</div>' +
                    '</div>' +
                '</div>';
            
            // Mejores parametros
            if (r.best_params) {
                html += '<div style="margin-bottom: 15px;">' +
                    '<div style="color: #8b949e; font-size: 12px; margin-bottom: 8px; font-weight: bold;">📊 Mejores Parametros:</div>' +
                    '<div style="background: #161b22; border-radius: 6px; padding: 10px;">';
                Object.keys(r.best_params).forEach(function(key) {
                    html += '<div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #30363d;">' +
                        '<span style="color: #e5e7eb;">' + key + '</span>' +
                        '<span style="color: #14b8a6; font-weight: bold;">' + r.best_params[key].toFixed(6) + '</span>' +
                    '</div>';
                });
                html += '</div></div>';
            }
            
            // Estadisticas
            html += '<div style="margin-bottom: 15px;">' +
                '<div style="color: #8b949e; font-size: 12px; margin-bottom: 8px; font-weight: bold;">📈 Estadisticas:</div>' +
                '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;">' +
                    '<div style="padding: 8px; background: #161b22; border-radius: 4px; text-align: center;">' +
                        '<div style="color: #6b7280; font-size: 10px;">Media</div>' +
                        '<div style="color: #e5e7eb; font-size: 12px;">' + (stats.mean || 0).toFixed(4) + '</div>' +
                    '</div>' +
                    '<div style="padding: 8px; background: #161b22; border-radius: 4px; text-align: center;">' +
                        '<div style="color: #6b7280; font-size: 10px;">Min</div>' +
                        '<div style="color: #22c55e; font-size: 12px;">' + (stats.min || 0).toFixed(4) + '</div>' +
                    '</div>' +
                    '<div style="padding: 8px; background: #161b22; border-radius: 4px; text-align: center;">' +
                        '<div style="color: #6b7280; font-size: 10px;">Max</div>' +
                        '<div style="color: #ef4444; font-size: 12px;">' + (stats.max || 0).toFixed(4) + '</div>' +
                    '</div>' +
                    '<div style="padding: 8px; background: #161b22; border-radius: 4px; text-align: center;">' +
                        '<div style="color: #6b7280; font-size: 10px;">Std</div>' +
                        '<div style="color: #f59e0b; font-size: 12px;">' + (stats.std || 0).toFixed(4) + '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';
            
            html += '<div style="color: #6b7280; font-size: 11px;">Tiempo: ' + (data.execution_time || 0).toFixed(3) + 's</div>';
            html += '</div>';
            
            outputDiv.innerHTML = html;
            showToast('MCTS completado: mejor valor = ' + (r.best_value || 0).toFixed(4), 'success');
        } else if (data.detail) {
            outputDiv.innerHTML = '<p style="color: #f85149;">Error: ' + data.detail + '</p>';
        } else {
            outputDiv.innerHTML = '<pre style="color: #e5e7eb; white-space: pre-wrap;">' + JSON.stringify(data, null, 2) + '</pre>';
        }
    } catch (e) {
        outputDiv.innerHTML = '<p style="color: #f85149;">Error: ' + e.message + '</p>';
    }
}
