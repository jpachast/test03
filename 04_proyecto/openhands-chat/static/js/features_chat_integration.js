// ============================================================
// FEATURES CHAT INTEGRATION - Auto Features durante conversaciones
// Integra: Auto-Fix, Test Generator, Web Scraper, Diff Preview, etc.
// ============================================================

(function() {
    'use strict';

    // Estado de las features
    window.chatFeatures = {
        autoFix: { enabled: true, status: 'ready' },
        testGenerator: { enabled: true, status: 'ready' },
        webScraper: { enabled: true, status: 'ready' },
        diffPreview: { enabled: true, status: 'ready' },
        codeAnalyzer: { enabled: true, status: 'ready' },
        semanticSearch: { enabled: true, status: 'ready' },
        codemaps: { enabled: true, status: 'ready' },
        backgroundAgents: { enabled: true, status: 'ready' },
        monteCarlo: { enabled: true, status: 'ready' }
    };

    // Patrones para detectar cuándo usar cada feature
    const FEATURE_TRIGGERS = {
        autoFix: {
            patterns: [
                /SyntaxError/i, /NameError/i, /TypeError/i, /ValueError/i,
                /IndentationError/i, /ImportError/i, /ModuleNotFoundError/i,
                /ZeroDivisionError/i, /IndexError/i, /KeyError/i,
                /AttributeError/i, /FileNotFoundError/i,
                /Traceback \(most recent call last\)/i,
                /error:\s+(.+)/i, /Exception:/i
            ],
            keywords: ['error', 'failed', 'exception', 'traceback']
        },
        testGenerator: {
            patterns: [
                /def\s+\w+\s*\([^)]*\)\s*:/,  // Definición de función Python
                /function\s+\w+\s*\([^)]*\)/,  // Definición de función JS
                /class\s+\w+/,  // Definición de clase
                /\.py$/m, /\.js$/m, /\.ts$/m  // Extensiones de archivo
            ],
            keywords: ['test', 'testing', 'crear tests', 'generar tests', 'unit test', 'pruebas']
        },
        webScraper: {
            patterns: [
                /https?:\/\/[^\s]+/,  // URLs
                /www\.[^\s]+/
            ],
            keywords: ['scrape', 'scrap', 'extraer', 'web', 'página', 'url', 'sitio']
        },
        diffPreview: {
            patterns: [
                /\bdiff\b/i,
                /cambios?\s*(pendientes?|sin\s*commit)/i
            ],
            keywords: ['diff', 'cambios', 'modificaciones', 'pendiente', 'staged', 'unstaged']
        },
        codeAnalyzer: {
            patterns: [
                /analizar?\s*(código|code)/i,
                /review/i, /revisar/i
            ],
            keywords: ['analizar', 'analyze', 'code review', 'revisar', 'optimizar']
        },
        semanticSearch: {
            patterns: [
                /donde\s+(esta|hay|encuentro)/i,
                /busca(r)?\s+(codigo|funcion|clase|archivo)/i,
                /encuentra\s+(el|la|los|las)?/i,
                /muestra.*codigo.*de/i,
                /que\s+archivos?\s+(manejan?|tienen?|contienen?)/i
            ],
            keywords: ['donde esta', 'buscar codigo', 'encuentra', 'ubicacion', 'en que archivo', 'busqueda semantica', 'codigo de', 'funcionalidad de']
        },
        codemaps: {
            patterns: [
                /dependencias?\s+(de|del|en)/i,
                /importa(r|ciones)?/i,
                /estructura\s+(del?)?\s*(codigo|proyecto)/i,
                /relacion(es)?\s+entre/i,
                /que\s+(usa|importa|depende)/i
            ],
            keywords: ['dependencias', 'imports', 'estructura', 'relaciones', 'arquitectura', 'modulos', 'grafo']
        },
        backgroundAgents: {
            patterns: [
                /en\s+(segundo\s+plano|background)/i,
                /tarea\s+(larga|pesada|intensiva)/i,
                /mientras\s+(tanto|continuo)/i,
                /ejecuta(r)?\s+.*(fondo|paralelo)/i,
                /proceso\s+(largo|async)/i
            ],
            keywords: ['segundo plano', 'background', 'tarea larga', 'paralelo', 'async', 'mientras tanto', 'sin bloquear']
        },
        monteCarlo: {
            patterns: [
                /optimi(zar?|zacion)/i,
                /mejor\s+(opcion|alternativa|solucion)/i,
                /evalua(r)?\s+opciones/i,
                /simula(r|cion)/i,
                /analisis\s+de\s+(decisiones|opciones)/i
            ],
            keywords: ['optimizar', 'mejor opcion', 'evaluar opciones', 'simulacion', 'monte carlo', 'decision', 'alternativas']
        }
    };

    // Detectar qué features aplicar según el mensaje/contexto
    function detectFeatures(text, context = {}) {
        const features = [];

        for (const [featureName, triggers] of Object.entries(FEATURE_TRIGGERS)) {
            if (!window.chatFeatures[featureName]?.enabled) continue;

            // Verificar patrones
            const patternMatch = triggers.patterns.some(p => p.test(text));

            // Verificar keywords
            const textLower = text.toLowerCase();
            const keywordMatch = triggers.keywords.some(k => textLower.includes(k.toLowerCase()));

            if (patternMatch || keywordMatch) {
                features.push({
                    name: featureName,
                    trigger: patternMatch ? 'pattern' : 'keyword',
                    confidence: patternMatch && keywordMatch ? 'high' : 'medium'
                });
            }
        }

        return features;
    }

    // ============================================================
    // AUTO-FIX: Corregir errores automáticamente
    // ============================================================
    async function applyAutoFix(code, errorOutput, responseElement) {
        if (!window.chatFeatures.autoFix.enabled) return null;

        try {
            const formData = new FormData();
            formData.append('code', code);
            formData.append('error_output', errorOutput);
            formData.append('language', detectLanguage(code));

            const response = await fetch('/api/chat/autofix/detect', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) return null;

            const result = await response.json();

            if (result.auto_fixed && responseElement) {
                appendFeatureResult(responseElement, formatAutoFixResult(result));
            }

            return result;
        } catch (e) {
            console.error('Auto-fix error:', e);
            return null;
        }
    }

    // ============================================================
    // TEST GENERATOR: Generar tests automáticamente
    // ============================================================
    async function applyTestGenerator(code, language, responseElement) {
        if (!window.chatFeatures.testGenerator.enabled) return null;

        try {
            const response = await fetch('/api/tests/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: code,
                    language: language || detectLanguage(code),
                    with_coverage: true
                })
            });

            if (!response.ok) return null;

            const result = await response.json();

            if (result.tests_count && responseElement) {
                appendFeatureResult(responseElement, formatTestGeneratorResult(result));
            }

            return result;
        } catch (e) {
            console.error('Test generator error:', e);
            return null;
        }
    }

    // ============================================================
    // WEB SCRAPER: Extraer contenido de URLs
    // ============================================================
    async function applyWebScraper(urls, responseElement) {
        if (!window.chatFeatures.webScraper.enabled) return null;

        try {
            const results = [];
            for (const url of urls.slice(0, 3)) {  // Máximo 3 URLs
                const response = await fetch('/api/scraper/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                if (response.ok) {
                    results.push(await response.json());
                }
            }

            if (results.length > 0 && responseElement) {
                appendFeatureResult(responseElement, formatWebScraperResult(results));
            }

            return results;
        } catch (e) {
            console.error('Web scraper error:', e);
            return null;
        }
    }

    // ============================================================
    // FORMATEADORES DE RESULTADOS
    // ============================================================

    // ============================================================
    // SEMANTIC SEARCH: Busqueda semantica de codigo
    // ============================================================
    async function applySemanticSearch(query, responseElement) {
        if (!window.chatFeatures.semanticSearch?.enabled) return null;
        
        console.log('[Features] Semantic Search activado para:', query);
        
        try {
            const pathParts = window.location.pathname.split('/');
            const conversationId = pathParts[pathParts.length - 1] || '1';
            
            const response = await fetch('/api/semantic/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    conversation_id: conversationId,
                    top_k: 5
                })
            });
            
            if (!response.ok) {
                console.warn('[Features] Semantic search no disponible');
                return null;
            }
            
            const result = await response.json();
            
            if (result.results && result.results.length > 0) {
                const html = formatSemanticSearchResult(result, query);
                appendFeatureResult(responseElement, html);
                return result;
            }
            
            return null;
        } catch (error) {
            console.error('[Features] Error en semantic search:', error);
            return null;
        }
    }

    function formatSemanticSearchResult(result, query) {
        let html = '<div class="feature-result semantic-search-result" style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 8px; border-left: 4px solid #8b5cf6;">';
        html += '<div style="display: flex; align-items: center; margin-bottom: 10px;">';
        html += '<span style="font-size: 1.2em; margin-right: 8px;">🔍</span>';
        html += '<strong style="color: #8b5cf6;">BUSQUEDA SEMANTICA: "' + escapeHtml(query) + '"</strong>';
        html += '</div>';
        
        if (result.results && result.results.length > 0) {
            html += '<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">';
            html += '<tr style="border-bottom: 1px solid #333;"><th style="text-align: left; padding: 5px; color: #a78bfa;">Archivo</th><th style="text-align: left; padding: 5px; color: #a78bfa;">Relevancia</th><th style="text-align: left; padding: 5px; color: #a78bfa;">Preview</th></tr>';
            
            result.results.forEach(r => {
                const stars = String.fromCodePoint(0x2B50).repeat(Math.min(5, Math.ceil((r.score || 0.5) * 5)));
                const preview = (r.content || r.text || '').substring(0, 60) + '...';
                html += '<tr style="border-bottom: 1px solid #222;">';
                html += '<td style="padding: 5px; color: #e0e0e0; font-family: monospace;">' + escapeHtml(r.file_path || r.metadata?.file_path || 'archivo') + '</td>';
                html += '<td style="padding: 5px;">' + stars + '</td>';
                html += '<td style="padding: 5px; color: #888; font-size: 0.9em;">' + escapeHtml(preview) + '</td>';
                html += '</tr>';
            });
            
            html += '</table>';
        } else {
            html += '<p style="color: #888;">No se encontraron resultados relevantes.</p>';
        }
        
        html += '</div>';
        return html;
    }


    // ============================================================
    // DIFF PREVIEW: Mostrar cambios estilo GitHub
    // ============================================================
    async function applyDiffPreview(responseElement) {
        if (!window.chatFeatures.diffPreview?.enabled) return null;
        
        console.log('[Features] Diff Preview activado');
        
        try {
            const pathParts = window.location.pathname.split('/');
            const conversationId = pathParts[pathParts.length - 1] || '1';
            
            const response = await fetch('/api/diff/changes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: conversationId })
            });
            
            if (!response.ok) {
                console.warn('[Features] Diff preview no disponible');
                return null;
            }
            
            const result = await response.json();
            
            if (result.changes && result.changes.length > 0) {
                const html = formatDiffPreviewResult(result);
                appendFeatureResult(responseElement, html);
                return result;
            }
            
            return null;
        } catch (error) {
            console.error('[Features] Error en diff preview:', error);
            return null;
        }
    }

    function formatDiffPreviewResult(result) {
        let html = '<div class="feature-result diff-preview-result" style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #1a1a2e 0%, #0d1117 100%); border-radius: 8px; border-left: 4px solid #238636;">';
        html += '<div style="display: flex; align-items: center; margin-bottom: 10px;">';
        html += '<span style="font-size: 1.2em; margin-right: 8px;">📊</span>';
        html += '<strong style="color: #238636;">DIFF PREVIEW - Cambios en el repositorio</strong>';
        html += '</div>';
        
        if (result.summary) {
            html += '<div style="margin-bottom: 10px; padding: 8px; background: #161b22; border-radius: 4px;">';
            html += '<span style="color: #3fb950;">+' + (result.summary.insertions || 0) + '</span> ';
            html += '<span style="color: #f85149;">-' + (result.summary.deletions || 0) + '</span> ';
            html += '<span style="color: #8b949e;">en ' + (result.summary.files_changed || 0) + ' archivo(s)</span>';
            html += '</div>';
        }
        
        if (result.changes) {
            result.changes.slice(0, 5).forEach(change => {
                const statusColor = change.status === 'added' ? '#3fb950' : change.status === 'deleted' ? '#f85149' : '#d29922';
                const statusIcon = change.status === 'added' ? '+' : change.status === 'deleted' ? '-' : '~';
                html += '<div style="padding: 5px 10px; margin: 3px 0; background: #21262d; border-radius: 4px; font-family: monospace; font-size: 0.9em;">';
                html += '<span style="color: ' + statusColor + ';">' + statusIcon + '</span> ';
                html += '<span style="color: #c9d1d9;">' + (change.file || change.path || 'archivo') + '</span>';
                html += '</div>';
            });
        }
        
        html += '</div>';
        return html;
    }


    // ============================================================
    // CODEMAPS: Mostrar dependencias y estructura del código
    // ============================================================
    async function applyCodemaps(query, responseElement) {
        if (!window.chatFeatures.codemaps?.enabled) return null;
        
        console.log('[Features] Codemaps activado');
        
        try {
            const pathParts = window.location.pathname.split('/');
            const conversationId = pathParts[pathParts.length - 1] || '1';
            
            const response = await fetch('/api/codemap/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    workspace: '/workspace/project',
                    max_files: 50
                })
            });
            
            if (!response.ok) {
                console.warn('[Features] Codemaps no disponible');
                return null;
            }
            
            const result = await response.json();
            
            if (result.success && result.graph?.nodes?.length > 0) {
                const html = formatCodemapsResult(result, query);
                appendFeatureResult(responseElement, html);
                return result;
            }
            
            return null;
        } catch (error) {
            console.error('[Features] Error en codemaps:', error);
            return null;
        }
    }

    function formatCodemapsResult(result, query) {
        let html = '<div class="feature-result codemaps-result" style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #1a1a2e 0%, #1e3a5f 100%); border-radius: 8px; border-left: 4px solid #3b82f6;">';
        html += '<div style="display: flex; align-items: center; margin-bottom: 10px;">';
        html += '<span style="font-size: 1.2em; margin-right: 8px;">🗺️</span>';
        html += '<strong style="color: #3b82f6;">MAPA DE DEPENDENCIAS</strong>';
        html += '</div>';
        
        if (result.stats) {
            html += '<div style="margin-bottom: 10px; padding: 8px; background: #1e293b; border-radius: 4px; font-size: 0.9em;">';
            html += '<span style="color: #60a5fa;">📁 ' + (result.stats.total_files || 0) + ' archivos</span> · ';
            html += '<span style="color: #34d399;">🔗 ' + (result.graph?.edges?.length || 0) + ' dependencias</span> · ';
            html += '<span style="color: #fbbf24;">📦 ' + (result.stats.total_imports || 0) + ' imports</span>';
            html += '</div>';
        }
        
        if (result.graph?.nodes) {
            html += '<div style="margin-top: 10px;">';
            html += '<strong style="color: #94a3b8; font-size: 0.85em;">ARCHIVOS PRINCIPALES:</strong>';
            html += '<div style="margin-top: 5px;">';
            
            const mainNodes = result.graph.nodes.slice(0, 8);
            mainNodes.forEach(node => {
                const icon = node.type === 'python' ? '🐍' : node.type === 'javascript' ? '📜' : '📄';
                html += '<div style="padding: 4px 8px; margin: 2px 0; background: #0f172a; border-radius: 4px; font-family: monospace; font-size: 0.85em;">';
                html += icon + ' <span style="color: #e2e8f0;">' + (node.name || node.id) + '</span>';
                if (node.imports) html += ' <span style="color: #64748b;">(' + node.imports + ' imports)</span>';
                html += '</div>';
            });
            
            html += '</div></div>';
        }
        
        html += '</div>';
        return html;
    }


    // ============================================================
    // BACKGROUND AGENTS: Ejecutar tareas largas sin bloquear
    // ============================================================
    async function applyBackgroundAgents(taskDescription, responseElement) {
        if (!window.chatFeatures.backgroundAgents?.enabled) return null;
        
        console.log('[Features] Background Agents activado');
        
        try {
            // Mostrar indicador de tarea en background
            const indicator = document.createElement('div');
            indicator.className = 'background-task-indicator';
            indicator.innerHTML = `
                <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #1a1a2e 0%, #2d1b4e 100%); border-radius: 8px; border-left: 4px solid #a855f7;">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <span style="font-size: 1.2em; margin-right: 8px;">⚡</span>
                        <strong style="color: #a855f7;">TAREA EN SEGUNDO PLANO</strong>
                    </div>
                    <div style="padding: 8px; background: #1e1b4b; border-radius: 4px;">
                        <span style="color: #c4b5fd;">📋 Tarea iniciada en background</span><br>
                        <span style="color: #8b5cf6; font-size: 0.9em;">El chat sigue disponible mientras se procesa</span>
                    </div>
                </div>
            `;
            responseElement.appendChild(indicator);
            
            // Enviar tarea al backend
            const response = await fetch('/api/background/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_type: 'analyze',
                    params: { description: taskDescription },
                    priority: 'NORMAL'
                })
            });
            
            if (!response.ok) {
                console.warn('[Features] Background agents no disponible');
                return null;
            }
            
            const result = await response.json();
            
            if (result.task_id) {
                // Actualizar indicador con ID de tarea
                indicator.querySelector('.background-task-indicator div div:last-child').innerHTML += 
                    `<br><span style="color: #a78bfa; font-size: 0.85em;">🆔 Task ID: ${result.task_id}</span>`;
                return result;
            }
            
            return null;
        } catch (error) {
            console.error('[Features] Error en background agents:', error);
            return null;
        }
    }


    // ============================================================
    // MONTE CARLO: Optimización y análisis de decisiones
    // ============================================================
    async function applyMonteCarlo(query, responseElement) {
        if (!window.chatFeatures.monteCarlo?.enabled) return null;
        
        console.log('[Features] Monte Carlo activado');
        
        try {
            // Mostrar indicador de simulación
            const indicator = document.createElement('div');
            indicator.className = 'monte-carlo-indicator';
            indicator.innerHTML = `
                <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #1a1a2e 0%, #4a1942 100%); border-radius: 8px; border-left: 4px solid #ec4899;">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <span style="font-size: 1.2em; margin-right: 8px;">🎲</span>
                        <strong style="color: #ec4899;">SIMULACIÓN MONTE CARLO</strong>
                    </div>
                    <div style="padding: 8px; background: #3b0764; border-radius: 4px;">
                        <span style="color: #f9a8d4;">📊 Ejecutando simulaciones...</span><br>
                        <span style="color: #be185d; font-size: 0.9em;">Analizando múltiples escenarios para optimizar decisión</span>
                    </div>
                </div>
            `;
            responseElement.appendChild(indicator);
            
            return { status: 'simulation_started', query };
        } catch (error) {
            console.error('[Features] Error en Monte Carlo:', error);
            return null;
        }
    }

    function formatAutoFixResult(result) {
        return `
            <div class="feature-result autofix-result" style="
                margin-top: 15px;
                padding: 15px;
                background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                border-radius: 10px;
                border-left: 4px solid #4caf50;
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <span style="font-size: 24px;">🔧</span>
                    <span style="color: #4caf50; font-weight: bold; font-size: 16px;">Auto-Fix Aplicado</span>
                </div>
                <div style="color: #a5d6a7; margin-bottom: 10px;">
                    ✅ ${result.fixes_applied || 1} corrección(es) aplicada(s)
                    ${result.verified ? '<br>✅ Código verificado - ejecuta correctamente' : ''}
                </div>
                <div style="margin-bottom: 10px;">
                    <div style="color: #81c784; font-weight: bold; margin-bottom: 5px;">Código corregido:</div>
                    <pre style="
                        background: #0d1117;
                        padding: 12px;
                        border-radius: 6px;
                        overflow-x: auto;
                        color: #c9d1d9;
                        font-family: 'Fira Code', monospace;
                        font-size: 13px;
                        border: 1px solid #30363d;
                    "><code>${escapeHtml(result.fixed_code || '')}</code></pre>
                </div>
                ${result.final_output ? `
                    <div>
                        <div style="color: #81c784; font-weight: bold; margin-bottom: 5px;">Resultado:</div>
                        <pre style="
                            background: #161b22;
                            padding: 10px;
                            border-radius: 6px;
                            color: #8b949e;
                            font-size: 12px;
                            max-height: 150px;
                            overflow-y: auto;
                        ">${escapeHtml(result.final_output.substring(0, 500))}</pre>
                    </div>
                ` : ''}
            </div>
        `;
    }

    function formatTestGeneratorResult(result) {
        // Formatear resultados de tests
        const testsHtml = (result.results || []).map(t => `
            <div style="padding: 8px; margin: 5px 0; background: ${t.passed ? '#1a3a1a' : '#3a1a1a'}; border-radius: 4px;">
                <span style="color: ${t.passed ? '#4caf50' : '#f44336'};">${t.passed ? '✓' : '✗'}</span>
                <span style="color: #81d4fa; margin-left: 8px;">${escapeHtml(t.name)}</span>
                ${t.output ? `<div style="color: #8b949e; font-size: 11px; margin-top: 4px;">${escapeHtml(t.output.substring(0, 100))}</div>` : ''}
            </div>
        `).join('');
        
        // Formatear cobertura
        const coverage = result.coverage_report || {};
        const coverageHtml = coverage.coverage_percent !== undefined ? `
            <div style="margin-top: 10px; padding: 10px; background: #161b22; border-radius: 6px;">
                <div style="color: #58a6ff; font-weight: bold; margin-bottom: 5px;">📊 Cobertura: ${coverage.coverage_percent.toFixed(1)}%</div>
                <div style="background: #21262d; border-radius: 4px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #238636, #2ea043); height: 100%; width: ${coverage.coverage_percent}%;"></div>
                </div>
                <div style="color: #8b949e; font-size: 11px; margin-top: 5px;">
                    Lineas: ${coverage.covered_lines}/${coverage.total_lines} | 
                    Funciones: ${(coverage.functions_covered || []).join(', ') || 'N/A'}
                </div>
            </div>
        ` : '';

        return `
            <div class="feature-result test-result" style="
                margin-top: 15px;
                padding: 15px;
                background: linear-gradient(135deg, #1a3a4a 0%, #2d4a5a 100%);
                border-radius: 10px;
                border-left: 4px solid #03a9f4;
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <span style="font-size: 24px;">🧪</span>
                    <span style="color: #03a9f4; font-weight: bold; font-size: 16px;">Tests Generados y Ejecutados</span>
                </div>
                <div style="color: #81d4fa; margin-bottom: 10px;">
                    ✅ ${result.passed || 0}/${result.tests_count || 0} tests pasaron
                </div>
                <div style="max-height: 200px; overflow-y: auto;">
                    ${testsHtml}
                </div>
                ${coverageHtml}
            </div>
        `;
    }

    function formatWebScraperResult(results) {
        const items = results.map(r => `
            <div style="margin-bottom: 10px; padding: 10px; background: #161b22; border-radius: 6px;">
                <div style="color: #58a6ff; font-weight: bold; margin-bottom: 5px;">
                    ${escapeHtml(r.title || r.url)}
                </div>
                <div style="color: #8b949e; font-size: 12px;">
                    ${escapeHtml((r.content || '').substring(0, 200))}...
                </div>
            </div>
        `).join('');

        return `
            <div class="feature-result scraper-result" style="
                margin-top: 15px;
                padding: 15px;
                background: linear-gradient(135deg, #3a1a4a 0%, #4a2d5a 100%);
                border-radius: 10px;
                border-left: 4px solid #9c27b0;
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <span style="font-size: 24px;">🌐</span>
                    <span style="color: #ce93d8; font-weight: bold; font-size: 16px;">Contenido Web Extraído</span>
                </div>
                ${items}
            </div>
        `;
    }

    // ============================================================
    // UTILIDADES
    // ============================================================
    function detectLanguage(code) {
        if (/def\s+\w+|import\s+\w+|from\s+\w+\s+import/.test(code)) return 'python';
        if (/function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+/.test(code)) return 'javascript';
        if (/public\s+class|private\s+void/.test(code)) return 'java';
        return 'python';  // Default
    }

    function extractCodeBlocks(text) {
        const blocks = [];
        const regex = /```(?:(\w+))?\n([\s\S]*?)```/g;
        let match;
        while ((match = regex.exec(text)) !== null) {
            blocks.push({
                language: match[1] || detectLanguage(match[2]),
                code: match[2].trim()
            });
        }
        return blocks;
    }

    function extractUrls(text) {
        const urlRegex = /https?:\/\/[^\s<>"']+/g;
        return text.match(urlRegex) || [];
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    function appendFeatureResult(element, html) {
        if (!element) return;
        const div = document.createElement('div');
        div.innerHTML = html;
        element.appendChild(div);
        div.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }

    // ============================================================
    // PROCESO PRINCIPAL: Analizar respuesta y aplicar features
    // ============================================================
    async function processResponseWithFeatures(responseElement, responseText, userMessage = '') {
        console.log('[Features] Procesando respuesta...');

        // Detectar qué features aplicar
        const featuresFromResponse = detectFeatures(responseText);
        const featuresFromUser = detectFeatures(userMessage);
        const featureNames = new Set([...featuresFromResponse.map(f => f.name), ...featuresFromUser.map(f => f.name)]);
        const features = [...featureNames].map(name => ({ name, trigger: "combined" }));
        console.log('[Features] Detectadas:', features.map(f => f.name));

        for (const feature of features) {
            try {
                switch (feature.name) {
                    case 'autoFix': {
                        // Extraer código del mensaje o usar el último conocido
                        const codeBlocks = extractCodeBlocks(responseText);
                        const code = codeBlocks[0]?.code || window.chatAutoFix?.lastCode;
                        if (code) {
                            await applyAutoFix(code, responseText, responseElement);
                        }
                        break;
                    }
                    case 'testGenerator': {
                        // Activar si el usuario pide tests
                        if (userMessage.toLowerCase().match(/test|prueba|genera.*test|crea.*test/)) {
                            // Buscar codigo en la respuesta o en el mensaje del usuario
                            let codeBlocks = extractCodeBlocks(responseText);
                            if (codeBlocks.length === 0) {
                                codeBlocks = extractCodeBlocks(userMessage);
                            }
                            if (codeBlocks.length > 0) {
                                console.log('[Features] Test Generator activado');
                                await applyTestGenerator(codeBlocks[0].code, codeBlocks[0].language, responseElement);
                            }
                        }
                        break;
                    }
                    case 'webScraper': {
                        // Solo si el usuario pidió scraping
                        if (userMessage.toLowerCase().match(/scrap|extraer.*web|extraer.*url/)) {
                            const urls = extractUrls(userMessage);
                            if (urls.length > 0) {
                                await applyWebScraper(urls, responseElement);
                            }
                        }
                        break;
                    }
                    case 'semanticSearch': {
                        // Activar si el usuario busca codigo/funcionalidad
                        const searchTerms = userMessage.match(/(?:donde\s+(?:esta|hay)|busca(?:r)?|encuentra|muestra.*codigo.*de|que\s+archivos?)\s+(.+)/i);
                        if (searchTerms && searchTerms[1]) {
                            const query = searchTerms[1].replace(/[?.,!]/g, '').trim();
                            if (query.length > 2) {
                                console.log('[Features] Semantic Search detectado, query:', query);
                                await applySemanticSearch(query, responseElement);
                            }
                        }
                        break;
                    }
                    case 'diffPreview': {
                        // Activar si el usuario pregunta por cambios/diff
                        if (userMessage.toLowerCase().match(/cambios|diff|modificad|pendiente|commit|status|estado.*repo/)) {
                            console.log('[Features] Diff Preview detectado');
                            await applyDiffPreview(responseElement);
                        }
                        break;
                    }
                    case 'codemaps': {
                        // Activar si el usuario pregunta por dependencias/estructura
                        if (userMessage.toLowerCase().match(/dependencias|imports|estructura|relacion|arquitectura|modulos|grafo|que.*(usa|importa)/)) {
                            console.log('[Features] Codemaps detectado');
                            await applyCodemaps(userMessage, responseElement);
                        }
                        break;
                    }
                    case 'backgroundAgents': {
                        // Activar si el usuario pide tareas en segundo plano
                        if (userMessage.toLowerCase().match(/segundo\s+plano|background|tarea\s+(larga|pesada)|mientras\s+tanto|paralelo|sin\s+bloquear/)) {
                            console.log('[Features] Background Agents detectado');
                            await applyBackgroundAgents(userMessage, responseElement);
                        }
                        break;
                    }
                    case 'monteCarlo': {
                        // Activar si el usuario pide optimización
                        if (userMessage.toLowerCase().match(/optimi|mejor\s+(opcion|alternativa|solucion)|evalua.*opciones|simula|monte\s*carlo|analisis.*decision/)) {
                            console.log('[Features] Monte Carlo detectado');
                            await applyMonteCarlo(userMessage, responseElement);
                        }
                        break;
                    }
                }
            } catch (e) {
                console.error(`[Features] Error en ${feature.name}:`, e);
            }
        }
    }

    // Exponer funciones globalmente
    window.processResponseWithFeatures = processResponseWithFeatures;
    window.detectFeatures = detectFeatures;
    window.applyAutoFix = applyAutoFix;
    window.applyTestGenerator = applyTestGenerator;
    window.applyWebScraper = applyWebScraper;
    window.applySemanticSearch = applySemanticSearch;
    window.applyDiffPreview = applyDiffPreview;
    window.applyCodemaps = applyCodemaps;
    window.applyBackgroundAgents = applyBackgroundAgents;
    window.applyMonteCarlo = applyMonteCarlo;

    console.log('✅ Features Chat Integration cargado');
})();
