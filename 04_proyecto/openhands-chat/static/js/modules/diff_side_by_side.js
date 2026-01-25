/**
 * Diff Side-by-Side Interactivo
 * Muestra diferencias de código con vista lado a lado
 */
(function() {
    'use strict';
    
    // Estado del módulo
    const state = {
        enabled: true,
        currentDiff: null,
        viewMode: 'side-by-side' // 'side-by-side', 'inline', 'unified'
    };
    
    // Estilos para el diff side-by-side
    const styles = `
        .diff-container {
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            border-radius: 8px;
            overflow: hidden;
            margin: 15px 0;
            border: 1px solid #30363d;
            background: #0d1117;
        }
        
        .diff-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            background: linear-gradient(135deg, #1a1a2e 0%, #161b22 100%);
            border-bottom: 1px solid #30363d;
        }
        
        .diff-title {
            color: #58a6ff;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .diff-controls {
            display: flex;
            gap: 5px;
        }
        
        .diff-btn {
            padding: 4px 12px;
            border: 1px solid #30363d;
            border-radius: 6px;
            background: #21262d;
            color: #c9d1d9;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }
        
        .diff-btn:hover {
            background: #30363d;
            border-color: #58a6ff;
        }
        
        .diff-btn.active {
            background: #238636;
            border-color: #238636;
            color: white;
        }
        
        .diff-side-by-side {
            display: grid;
            grid-template-columns: 1fr 1fr;
        }
        
        .diff-panel {
            overflow-x: auto;
        }
        
        .diff-panel-header {
            padding: 8px 15px;
            background: #161b22;
            color: #8b949e;
            font-size: 12px;
            border-bottom: 1px solid #30363d;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .diff-panel-left {
            border-right: 1px solid #30363d;
        }
        
        .diff-panel-left .diff-panel-header {
            color: #f85149;
        }
        
        .diff-panel-right .diff-panel-header {
            color: #3fb950;
        }
        
        .diff-content {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .diff-line {
            display: flex;
            min-height: 22px;
            line-height: 22px;
        }
        
        .diff-line-number {
            min-width: 45px;
            padding: 0 10px;
            text-align: right;
            color: #484f58;
            background: #161b22;
            user-select: none;
            border-right: 1px solid #21262d;
        }
        
        .diff-line-content {
            flex: 1;
            padding: 0 10px;
            white-space: pre;
            overflow-x: auto;
        }
        
        .diff-line-added {
            background: rgba(46, 160, 67, 0.15);
        }
        
        .diff-line-added .diff-line-content {
            color: #3fb950;
        }
        
        .diff-line-added .diff-line-number {
            background: rgba(46, 160, 67, 0.2);
            color: #3fb950;
        }
        
        .diff-line-removed {
            background: rgba(248, 81, 73, 0.15);
        }
        
        .diff-line-removed .diff-line-content {
            color: #f85149;
        }
        
        .diff-line-removed .diff-line-number {
            background: rgba(248, 81, 73, 0.2);
            color: #f85149;
        }
        
        .diff-line-context {
            background: transparent;
        }
        
        .diff-line-context .diff-line-content {
            color: #8b949e;
        }
        
        .diff-line-empty {
            background: #161b22;
        }
        
        .diff-stats {
            display: flex;
            gap: 15px;
            padding: 10px 15px;
            background: #161b22;
            border-top: 1px solid #30363d;
            font-size: 12px;
        }
        
        .diff-stat-added {
            color: #3fb950;
        }
        
        .diff-stat-removed {
            color: #f85149;
        }
        
        .diff-stat-files {
            color: #58a6ff;
        }
        
        /* Vista inline */
        .diff-inline .diff-line {
            display: flex;
        }
        
        .diff-inline .diff-line-added::before {
            content: '+';
            color: #3fb950;
            padding-right: 8px;
        }
        
        .diff-inline .diff-line-removed::before {
            content: '-';
            color: #f85149;
            padding-right: 8px;
        }
        
        /* Highlight de sintaxis básico */
        .diff-keyword { color: #ff7b72; }
        .diff-string { color: #a5d6ff; }
        .diff-comment { color: #8b949e; font-style: italic; }
        .diff-function { color: #d2a8ff; }
        .diff-number { color: #79c0ff; }
        
        /* Animación de entrada */
        .diff-container {
            animation: diffFadeIn 0.3s ease-out;
        }
        
        @keyframes diffFadeIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Interactividad */
        .diff-line:hover {
            background: rgba(88, 166, 255, 0.1);
        }
        
        .diff-line-clickable {
            cursor: pointer;
        }
        
        .diff-line-clickable:hover {
            background: rgba(88, 166, 255, 0.2);
        }
        
        /* Botones de acción */
        .diff-actions {
            display: flex;
            gap: 10px;
            padding: 10px 15px;
            background: #161b22;
            border-top: 1px solid #30363d;
        }
        
        .diff-action-btn {
            padding: 6px 16px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
        }
        
        .diff-action-btn.primary {
            background: #238636;
            color: white;
        }
        
        .diff-action-btn.primary:hover {
            background: #2ea043;
        }
        
        .diff-action-btn.secondary {
            background: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
        }
        
        .diff-action-btn.secondary:hover {
            background: #30363d;
        }
    `;
    
    // Inyectar estilos
    function injectStyles() {
        if (document.getElementById('diff-side-by-side-styles')) return;
        const styleEl = document.createElement('style');
        styleEl.id = 'diff-side-by-side-styles';
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);
    }
    
    // Parsear diff unificado
    function parseDiff(diffText) {
        const lines = diffText.split('\n');
        const files = [];
        let currentFile = null;
        let oldLine = 0, newLine = 0;
        
        for (const line of lines) {
            if (line.startsWith('diff --git') || line.startsWith('--- ') && !currentFile) {
                if (currentFile) files.push(currentFile);
                currentFile = {
                    oldFile: '',
                    newFile: '',
                    chunks: [],
                    currentChunk: null
                };
            }
            
            if (line.startsWith('--- a/')) {
                currentFile.oldFile = line.substring(6);
            } else if (line.startsWith('+++ b/')) {
                currentFile.newFile = line.substring(6);
            } else if (line.startsWith('@@')) {
                const match = line.match(/@@ -(\d+),?\d* \+(\d+),?\d* @@/);
                if (match) {
                    oldLine = parseInt(match[1]) - 1;
                    newLine = parseInt(match[2]) - 1;
                    if (!currentFile.chunks) currentFile.chunks = [];
                    currentFile.currentChunk = { lines: [] };
                    currentFile.chunks.push(currentFile.currentChunk);
                }
            } else if (currentFile && currentFile.currentChunk) {
                if (line.startsWith('+') && !line.startsWith('+++')) {
                    newLine++;
                    currentFile.currentChunk.lines.push({
                        type: 'added',
                        content: line.substring(1),
                        oldLineNum: null,
                        newLineNum: newLine
                    });
                } else if (line.startsWith('-') && !line.startsWith('---')) {
                    oldLine++;
                    currentFile.currentChunk.lines.push({
                        type: 'removed',
                        content: line.substring(1),
                        oldLineNum: oldLine,
                        newLineNum: null
                    });
                } else if (line.startsWith(' ')) {
                    oldLine++;
                    newLine++;
                    currentFile.currentChunk.lines.push({
                        type: 'context',
                        content: line.substring(1),
                        oldLineNum: oldLine,
                        newLineNum: newLine
                    });
                }
            }
        }
        
        if (currentFile) files.push(currentFile);
        return files;
    }
    
    // Calcular estadísticas
    function calculateStats(files) {
        let added = 0, removed = 0;
        for (const file of files) {
            for (const chunk of (file.chunks || [])) {
                for (const line of (chunk.lines || [])) {
                    if (line.type === 'added') added++;
                    if (line.type === 'removed') removed++;
                }
            }
        }
        return { added, removed, files: files.length };
    }
    
    // Highlight básico de sintaxis
    function highlightSyntax(content) {
        return content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/(["'`])([^"'`]*)\1/g, '<span class="diff-string">$1$2$1</span>')
            .replace(/\b(function|const|let|var|return|if|else|for|while|class|import|export|from|async|await|def|self|True|False|None)\b/g, '<span class="diff-keyword">$1</span>')
            .replace(/\b(\d+)\b/g, '<span class="diff-number">$1</span>')
            .replace(/(\/\/.*$|#.*$)/gm, '<span class="diff-comment">$1</span>');
    }
    
    // Renderizar vista side-by-side
    function renderSideBySide(files) {
        let html = '';
        
        for (const file of files) {
            const leftLines = [];
            const rightLines = [];
            
            for (const chunk of (file.chunks || [])) {
                for (const line of (chunk.lines || [])) {
                    if (line.type === 'removed') {
                        leftLines.push(line);
                    } else if (line.type === 'added') {
                        rightLines.push(line);
                    } else {
                        // Contexto: agregar a ambos lados
                        leftLines.push(line);
                        rightLines.push(line);
                    }
                }
            }
            
            // Balancear las líneas
            const maxLines = Math.max(leftLines.length, rightLines.length);
            while (leftLines.length < maxLines) leftLines.push({ type: 'empty', content: '', oldLineNum: null });
            while (rightLines.length < maxLines) rightLines.push({ type: 'empty', content: '', newLineNum: null });
            
            html += `
                <div class="diff-side-by-side">
                    <div class="diff-panel diff-panel-left">
                        <div class="diff-panel-header">
                            <span>📄</span>
                            <span>${file.oldFile || 'Original'}</span>
                        </div>
                        <div class="diff-content">
                            ${leftLines.map(line => `
                                <div class="diff-line diff-line-${line.type}">
                                    <span class="diff-line-number">${line.oldLineNum || ''}</span>
                                    <span class="diff-line-content">${highlightSyntax(line.content)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="diff-panel diff-panel-right">
                        <div class="diff-panel-header">
                            <span>📄</span>
                            <span>${file.newFile || 'Modificado'}</span>
                        </div>
                        <div class="diff-content">
                            ${rightLines.map(line => `
                                <div class="diff-line diff-line-${line.type}">
                                    <span class="diff-line-number">${line.newLineNum || ''}</span>
                                    <span class="diff-line-content">${highlightSyntax(line.content)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        return html;
    }
    
    // Renderizar vista inline
    function renderInline(files) {
        let html = '<div class="diff-inline">';
        
        for (const file of files) {
            html += `<div class="diff-file-header" style="padding: 10px; background: #161b22; color: #58a6ff; border-bottom: 1px solid #30363d;">📄 ${file.newFile || file.oldFile}</div>`;
            html += '<div class="diff-content">';
            
            for (const chunk of (file.chunks || [])) {
                for (const line of (chunk.lines || [])) {
                    const lineNum = line.oldLineNum || line.newLineNum || '';
                    html += `
                        <div class="diff-line diff-line-${line.type}">
                            <span class="diff-line-number">${lineNum}</span>
                            <span class="diff-line-content">${highlightSyntax(line.content)}</span>
                        </div>
                    `;
                }
            }
            
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }
    
    // Crear componente de diff completo
    function createDiffComponent(diffText, options = {}) {
        const files = parseDiff(diffText);
        const stats = calculateStats(files);
        state.currentDiff = { diffText, files, stats };
        
        const container = document.createElement('div');
        container.className = 'diff-container';
        container.innerHTML = `
            <div class="diff-header">
                <div class="diff-title">
                    <span>📊</span>
                    <span>Diff Side-by-Side</span>
                </div>
                <div class="diff-controls">
                    <button class="diff-btn active" data-mode="side-by-side">⬛⬛ Side-by-Side</button>
                    <button class="diff-btn" data-mode="inline">📄 Inline</button>
                </div>
            </div>
            <div class="diff-body">
                ${renderSideBySide(files)}
            </div>
            <div class="diff-stats">
                <span class="diff-stat-files">📁 ${stats.files} archivo(s)</span>
                <span class="diff-stat-added">+${stats.added} agregadas</span>
                <span class="diff-stat-removed">-${stats.removed} eliminadas</span>
            </div>
            ${options.showActions ? `
                <div class="diff-actions">
                    <button class="diff-action-btn primary" onclick="window.DiffSideBySide.applyChanges()">✓ Aplicar cambios</button>
                    <button class="diff-action-btn secondary" onclick="window.DiffSideBySide.revertChanges()">↩ Revertir</button>
                    <button class="diff-action-btn secondary" onclick="window.DiffSideBySide.copyDiff()">📋 Copiar diff</button>
                </div>
            ` : ''}
        `;
        
        // Event listeners para cambiar vista
        container.querySelectorAll('.diff-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                container.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const body = container.querySelector('.diff-body');
                if (mode === 'side-by-side') {
                    body.innerHTML = renderSideBySide(files);
                } else {
                    body.innerHTML = renderInline(files);
                }
            });
        });
        
        return container;
    }
    
    // Crear diff desde dos textos
    function createDiffFromTexts(oldText, newText, fileName = 'archivo') {
        const oldLines = oldText.split('\n');
        const newLines = newText.split('\n');
        
        // Algoritmo simple de diff
        let diffText = `diff --git a/${fileName} b/${fileName}\n`;
        diffText += `--- a/${fileName}\n`;
        diffText += `+++ b/${fileName}\n`;
        diffText += `@@ -1,${oldLines.length} +1,${newLines.length} @@\n`;
        
        // LCS básico para detectar cambios
        const maxLen = Math.max(oldLines.length, newLines.length);
        for (let i = 0; i < maxLen; i++) {
            const oldLine = oldLines[i];
            const newLine = newLines[i];
            
            if (oldLine === newLine) {
                if (oldLine !== undefined) diffText += ` ${oldLine}\n`;
            } else {
                if (oldLine !== undefined) diffText += `-${oldLine}\n`;
                if (newLine !== undefined) diffText += `+${newLine}\n`;
            }
        }
        
        return createDiffComponent(diffText);
    }
    
    // Integración con el chat
    function integrateDiffInChat(messageElement, diffData) {
        if (!messageElement || !diffData) return;
        
        injectStyles();
        
        const diffComponent = createDiffComponent(diffData);
        messageElement.appendChild(diffComponent);
    }
    
    // Detectar bloques de diff en respuestas
    function detectAndRenderDiffs(element) {
        if (!element) return;
        
        injectStyles();
        
        // Buscar bloques de código con diff
        const codeBlocks = element.querySelectorAll('pre code');
        
        codeBlocks.forEach(block => {
            const text = block.textContent;
            
            // Detectar si es un diff
            if (text.includes('diff --git') || 
                (text.includes('--- ') && text.includes('+++ ')) ||
                (text.match(/^[-+@]/m) && text.match(/^[-+]/m))) {
                
                const pre = block.parentElement;
                const diffComponent = createDiffComponent(text);
                pre.replaceWith(diffComponent);
            }
        });
    }
    
    // Copiar diff al portapapeles
    function copyDiff() {
        if (state.currentDiff) {
            navigator.clipboard.writeText(state.currentDiff.diffText);
            if (window.showToast) {
                window.showToast('Diff copiado al portapapeles', 'success');
            }
        }
    }
    
    // Inicializar
    function init() {
        injectStyles();
        console.log('[DiffSideBySide] Módulo inicializado');
    }
    
    // Inicializar cuando DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Exponer API global
    window.DiffSideBySide = {
        create: createDiffComponent,
        createFromTexts: createDiffFromTexts,
        integrate: integrateDiffInChat,
        detect: detectAndRenderDiffs,
        copyDiff: copyDiff,
        getState: () => state,
        applyChanges: () => console.log('Aplicar cambios...'),
        revertChanges: () => console.log('Revertir cambios...')
    };
    
})();
