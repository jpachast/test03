/**
 * Context Manager Module - RAG + Compresión Inteligente
 * Gestiona la ventana de contexto, aplica RAG y compresión
 */
(function() {
    'use strict';
    
    // Estado del contexto
    const state = {
        maxTokens: 128000,  // Límite típico de contexto (GPT-4)
        usedTokens: 0,
        compressionEnabled: true,
        ragEnabled: true,
        ragResults: [],
        contextHistory: []
    };
    
    // Estilos CSS
    function injectStyles() {
        if (document.getElementById('context-manager-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'context-manager-styles';
        styles.textContent = `
            /* Indicador de contexto en la barra */
            .context-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 12px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-radius: 20px;
                font-size: 12px;
                color: #ddd;
                border: 1px solid #333;
            }
            
            .context-indicator:hover {
                border-color: #0f3460;
                cursor: pointer;
            }
            
            .context-bar {
                width: 80px;
                height: 6px;
                background: #333;
                border-radius: 3px;
                overflow: hidden;
            }
            
            .context-bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #4caf50, #8bc34a);
                border-radius: 3px;
                transition: width 0.3s ease;
            }
            
            .context-bar-fill.warning {
                background: linear-gradient(90deg, #ff9800, #ffc107);
            }
            
            .context-bar-fill.danger {
                background: linear-gradient(90deg, #f44336, #ff5722);
            }
            
            /* Panel de RAG */
            .rag-panel {
                position: fixed;
                bottom: 80px;
                left: 20px;
                width: 350px;
                max-height: 400px;
                background: #1e1e2e;
                border-radius: 12px;
                border: 1px solid #333;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
                z-index: 1000;
                display: none;
                overflow: hidden;
            }
            
            .rag-panel.show {
                display: block;
                animation: slideUp 0.2s ease;
            }
            
            @keyframes slideUp {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            .rag-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 15px;
                background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
                border-bottom: 1px solid #333;
            }
            
            .rag-title {
                font-weight: bold;
                color: #e94560;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .rag-close {
                background: none;
                border: none;
                color: #888;
                font-size: 18px;
                cursor: pointer;
            }
            
            .rag-close:hover {
                color: #fff;
            }
            
            .rag-content {
                padding: 15px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .rag-section {
                margin-bottom: 15px;
            }
            
            .rag-section-title {
                font-size: 11px;
                text-transform: uppercase;
                color: #888;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .rag-toggle {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 10px;
                background: #2a2a3a;
                border-radius: 8px;
                margin-bottom: 8px;
            }
            
            .rag-toggle-label {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #ddd;
            }
            
            .rag-switch {
                position: relative;
                width: 40px;
                height: 20px;
                background: #444;
                border-radius: 10px;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .rag-switch.active {
                background: #4caf50;
            }
            
            .rag-switch::after {
                content: '';
                position: absolute;
                top: 2px;
                left: 2px;
                width: 16px;
                height: 16px;
                background: white;
                border-radius: 50%;
                transition: transform 0.2s;
            }
            
            .rag-switch.active::after {
                transform: translateX(20px);
            }
            
            /* Resultados de RAG */
            .rag-results {
                max-height: 150px;
                overflow-y: auto;
            }
            
            .rag-result-item {
                padding: 8px 10px;
                background: #2a2a3a;
                border-radius: 6px;
                margin-bottom: 6px;
                font-size: 12px;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .rag-result-item:hover {
                background: #3a3a4a;
            }
            
            .rag-result-file {
                color: #4ec9b0;
                font-family: monospace;
            }
            
            .rag-result-preview {
                color: #888;
                margin-top: 4px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .rag-result-score {
                float: right;
                background: #0f3460;
                color: #4ec9b0;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 10px;
            }
            
            /* Estadísticas de contexto */
            .context-stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            
            .context-stat {
                padding: 8px;
                background: #2a2a3a;
                border-radius: 6px;
                text-align: center;
            }
            
            .context-stat-value {
                font-size: 16px;
                font-weight: bold;
                color: #4caf50;
            }
            
            .context-stat-label {
                font-size: 10px;
                color: #888;
                margin-top: 2px;
            }
            
            /* Badge en respuestas */
            .rag-badge {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 3px 8px;
                background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
                border-radius: 12px;
                font-size: 11px;
                color: #4ec9b0;
                margin-left: 8px;
            }
            
            .compression-badge {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 3px 8px;
                background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                border-radius: 12px;
                font-size: 11px;
                color: #8bc34a;
                margin-left: 8px;
            }
            
            /* Tooltip de contexto */
            .context-tooltip {
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background: #1e1e2e;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 10px;
                min-width: 200px;
                display: none;
                z-index: 1001;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            
            .context-indicator:hover .context-tooltip {
                display: block;
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Estimar tokens (aproximación simple: 1 token ≈ 4 caracteres)
    function estimateTokens(text) {
        if (!text) return 0;
        return Math.ceil(text.length / 4);
    }
    
    // Comprimir texto inteligentemente
    function compressText(text, targetTokens) {
        if (!text) return { text: '', compressed: false, ratio: 1 };
        
        const originalTokens = estimateTokens(text);
        if (originalTokens <= targetTokens) {
            return { text, compressed: false, ratio: 1 };
        }
        
        // Estrategias de compresión
        let compressed = text;
        
        // 1. Eliminar comentarios largos
        compressed = compressed.replace(/\/\*[\s\S]*?\*\//g, '/* ... */');
        compressed = compressed.replace(/\/\/.*$/gm, '');
        
        // 2. Reducir espacios múltiples
        compressed = compressed.replace(/\n\s*\n\s*\n/g, '\n\n');
        compressed = compressed.replace(/  +/g, ' ');
        
        // 3. Si aún es muy largo, truncar con resumen
        const compressedTokens = estimateTokens(compressed);
        if (compressedTokens > targetTokens) {
            const ratio = targetTokens / compressedTokens;
            const keepChars = Math.floor(compressed.length * ratio * 0.9);
            compressed = compressed.substring(0, keepChars) + '\n... [comprimido]';
        }
        
        return {
            text: compressed,
            compressed: true,
            ratio: estimateTokens(compressed) / originalTokens
        };
    }
    
    // Buscar contexto relevante con RAG
    async function searchRAG(query, projectPath) {
        if (!state.ragEnabled) return [];
        
        try {
            const response = await fetch('/api/semantic/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    project_path: projectPath,
                    limit: 5
                })
            });
            
            if (!response.ok) return [];
            
            const data = await response.json();
            state.ragResults = data.results || [];
            return state.ragResults;
        } catch (e) {
            console.error('[ContextManager] Error en RAG:', e);
            return [];
        }
    }
    
    // Crear indicador de contexto
    function createContextIndicator() {
        const existing = document.getElementById('contextIndicator');
        if (existing) return existing;
        
        const indicator = document.createElement('div');
        indicator.id = 'contextIndicator';
        indicator.className = 'context-indicator';
        indicator.innerHTML = `
            <span>📊</span>
            <div class="context-bar">
                <div class="context-bar-fill" style="width: 0%"></div>
            </div>
            <span class="context-percent">0%</span>
            <div class="context-tooltip">
                <div style="font-weight: bold; margin-bottom: 8px;">Ventana de Contexto</div>
                <div class="context-stats">
                    <div class="context-stat">
                        <div class="context-stat-value" id="usedTokensDisplay">0</div>
                        <div class="context-stat-label">Tokens usados</div>
                    </div>
                    <div class="context-stat">
                        <div class="context-stat-value" id="maxTokensDisplay">128K</div>
                        <div class="context-stat-label">Límite</div>
                    </div>
                </div>
            </div>
        `;
        
        indicator.onclick = () => toggleRAGPanel();
        
        // Insertar en la barra de herramientas
        const toolbar = document.querySelector('.chat-toolbar') || document.querySelector('.chat-input-container');
        if (toolbar) {
            toolbar.appendChild(indicator);
        }
        
        return indicator;
    }
    
    // Crear panel de RAG
    function createRAGPanel() {
        const existing = document.getElementById('ragPanel');
        if (existing) return existing;
        
        const panel = document.createElement('div');
        panel.id = 'ragPanel';
        panel.className = 'rag-panel';
        panel.innerHTML = `
            <div class="rag-header">
                <div class="rag-title">
                    <span>🧠</span>
                    <span>RAG + Compresión</span>
                </div>
                <button class="rag-close" onclick="window.ContextManager.closePanel()">×</button>
            </div>
            <div class="rag-content">
                <div class="rag-section">
                    <div class="rag-section-title">⚙️ Configuración</div>
                    <div class="rag-toggle">
                        <div class="rag-toggle-label">
                            <span>🔍</span>
                            <span>RAG (Búsqueda semántica)</span>
                        </div>
                        <div class="rag-switch ${state.ragEnabled ? 'active' : ''}" onclick="window.ContextManager.toggleRAG()"></div>
                    </div>
                    <div class="rag-toggle">
                        <div class="rag-toggle-label">
                            <span>📦</span>
                            <span>Compresión inteligente</span>
                        </div>
                        <div class="rag-switch ${state.compressionEnabled ? 'active' : ''}" onclick="window.ContextManager.toggleCompression()"></div>
                    </div>
                </div>
                
                <div class="rag-section">
                    <div class="rag-section-title">📊 Estado del contexto</div>
                    <div class="context-stats">
                        <div class="context-stat">
                            <div class="context-stat-value" id="panelUsedTokens">${formatTokens(state.usedTokens)}</div>
                            <div class="context-stat-label">Usados</div>
                        </div>
                        <div class="context-stat">
                            <div class="context-stat-value" id="panelMaxTokens">${formatTokens(state.maxTokens)}</div>
                            <div class="context-stat-label">Límite</div>
                        </div>
                        <div class="context-stat">
                            <div class="context-stat-value" id="panelCompressionRatio">1.0x</div>
                            <div class="context-stat-label">Compresión</div>
                        </div>
                        <div class="context-stat">
                            <div class="context-stat-value" id="panelRAGResults">0</div>
                            <div class="context-stat-label">RAG hits</div>
                        </div>
                    </div>
                </div>
                
                <div class="rag-section" id="ragResultsSection" style="display: none;">
                    <div class="rag-section-title">🔍 Contexto RAG recuperado</div>
                    <div class="rag-results" id="ragResultsList"></div>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        return panel;
    }
    
    // Formatear tokens
    function formatTokens(tokens) {
        if (tokens >= 1000000) return (tokens / 1000000).toFixed(1) + 'M';
        if (tokens >= 1000) return (tokens / 1000).toFixed(1) + 'K';
        return tokens.toString();
    }
    
    // Actualizar indicador visual
    function updateIndicator() {
        const indicator = document.getElementById('contextIndicator');
        if (!indicator) return;
        
        const percent = Math.min((state.usedTokens / state.maxTokens) * 100, 100);
        const fill = indicator.querySelector('.context-bar-fill');
        const percentText = indicator.querySelector('.context-percent');
        
        fill.style.width = percent + '%';
        percentText.textContent = Math.round(percent) + '%';
        
        // Cambiar color según uso
        fill.classList.remove('warning', 'danger');
        if (percent > 80) {
            fill.classList.add('danger');
        } else if (percent > 60) {
            fill.classList.add('warning');
        }
        
        // Actualizar displays
        const usedDisplay = document.getElementById('usedTokensDisplay');
        if (usedDisplay) usedDisplay.textContent = formatTokens(state.usedTokens);
        
        const panelUsed = document.getElementById('panelUsedTokens');
        if (panelUsed) panelUsed.textContent = formatTokens(state.usedTokens);
        
        const panelRAG = document.getElementById('panelRAGResults');
        if (panelRAG) panelRAG.textContent = state.ragResults.length;
    }
    
    // Toggle panel
    function toggleRAGPanel() {
        const panel = document.getElementById('ragPanel') || createRAGPanel();
        panel.classList.toggle('show');
    }
    
    function closePanel() {
        const panel = document.getElementById('ragPanel');
        if (panel) panel.classList.remove('show');
    }
    
    // Toggle RAG
    function toggleRAG() {
        state.ragEnabled = !state.ragEnabled;
        const switches = document.querySelectorAll('.rag-switch');
        if (switches[0]) {
            switches[0].classList.toggle('active', state.ragEnabled);
        }
        console.log('[ContextManager] RAG:', state.ragEnabled ? 'ON' : 'OFF');
    }
    
    // Toggle Compresión
    function toggleCompression() {
        state.compressionEnabled = !state.compressionEnabled;
        const switches = document.querySelectorAll('.rag-switch');
        if (switches[1]) {
            switches[1].classList.toggle('active', state.compressionEnabled);
        }
        console.log('[ContextManager] Compresión:', state.compressionEnabled ? 'ON' : 'OFF');
    }
    
    // Mostrar resultados RAG
    function showRAGResults(results) {
        const section = document.getElementById('ragResultsSection');
        const list = document.getElementById('ragResultsList');
        
        if (!section || !list) return;
        
        if (results.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        list.innerHTML = results.map(r => `
            <div class="rag-result-item" onclick="window.ContextManager.openFile('${r.file}', ${r.line})">
                <span class="rag-result-score">${Math.round(r.score * 100)}%</span>
                <div class="rag-result-file">${r.file}:${r.line}</div>
                <div class="rag-result-preview">${(r.preview || r.content || '').substring(0, 60)}...</div>
            </div>
        `).join('');
    }
    
    // Agregar badge a mensaje
    function addBadgeToMessage(element, type, info) {
        if (!element) return;
        
        const existingBadge = element.querySelector(`.${type}-badge`);
        if (existingBadge) return;
        
        const badge = document.createElement('span');
        badge.className = `${type}-badge`;
        
        if (type === 'rag') {
            badge.innerHTML = `🔍 RAG: ${info.hits} hits`;
        } else if (type === 'compression') {
            badge.innerHTML = `📦 ${info.ratio}x comprimido`;
        }
        
        // Insertar al inicio del mensaje
        const content = element.querySelector('.message-content') || element;
        content.insertBefore(badge, content.firstChild);
    }
    
    // Procesar mensaje antes de enviar
    async function processMessage(message, conversationHistory) {
        const result = {
            message: message,
            context: '',
            ragUsed: false,
            compressionUsed: false,
            compressionRatio: 1
        };
        
        // Estimar tokens actuales
        let totalTokens = estimateTokens(message);
        if (conversationHistory) {
            totalTokens += estimateTokens(JSON.stringify(conversationHistory));
        }
        
        // Buscar con RAG si está habilitado
        if (state.ragEnabled) {
            const projectPath = window.currentProject || '';
            const ragResults = await searchRAG(message, projectPath);
            
            if (ragResults.length > 0) {
                result.ragUsed = true;
                state.ragResults = ragResults;
                
                // Agregar contexto RAG
                const ragContext = ragResults.map(r => 
                    `// ${r.file}:${r.line}\n${r.content}`
                ).join('\n\n');
                
                result.context = ragContext;
                totalTokens += estimateTokens(ragContext);
                
                showRAGResults(ragResults);
            }
        }
        
        // Comprimir si excede el límite
        if (state.compressionEnabled && totalTokens > state.maxTokens * 0.8) {
            const targetTokens = Math.floor(state.maxTokens * 0.6);
            const compressed = compressText(result.context + '\n' + result.message, targetTokens);
            
            if (compressed.compressed) {
                result.compressionUsed = true;
                result.compressionRatio = compressed.ratio;
                result.message = compressed.text;
            }
        }
        
        state.usedTokens = totalTokens;
        updateIndicator();
        
        return result;
    }
    
    // Detectar y mostrar badges en respuestas
    function detectAndShowBadges(element) {
        if (!element) return;
        
        // Si se usó RAG, mostrar badge
        if (state.ragResults.length > 0 && state.ragEnabled) {
            addBadgeToMessage(element, 'rag', { hits: state.ragResults.length });
        }
    }
    
    // Abrir archivo desde RAG
    function openFile(file, line) {
        console.log(`[ContextManager] Abrir ${file}:${line}`);
        // Integrar con el editor si está disponible
        if (window.openFileInEditor) {
            window.openFileInEditor(file, line);
        }
    }
    
    // Inicializar
    function init() {
        injectStyles();
        createContextIndicator();
        createRAGPanel();
        
        console.log('[ContextManager] RAG + Compresión inicializado');
        
        // Observer para detectar respuestas
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1 && node.classList && 
                            node.classList.contains('message') && 
                            node.classList.contains('assistant')) {
                            setTimeout(() => detectAndShowBadges(node), 500);
                        }
                    });
                });
            });
            
            observer.observe(chatMessages, { childList: true, subtree: true });
        }
    }
    
    // Inicializar cuando DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 1500);
    }
    
    // Exponer API global
    window.ContextManager = {
        init: init,
        process: processMessage,
        searchRAG: searchRAG,
        compress: compressText,
        estimateTokens: estimateTokens,
        toggleRAG: toggleRAG,
        toggleCompression: toggleCompression,
        togglePanel: toggleRAGPanel,
        closePanel: closePanel,
        showRAGResults: showRAGResults,
        openFile: openFile,
        updateIndicator: updateIndicator,
        getState: () => ({ ...state })
    };
    
})();
