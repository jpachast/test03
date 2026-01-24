
/**
 * Diff Preview Visual - Estilo GitHub
 * Muestra cambios en código con colores verde/rojo
 */

class DiffPreview {
    constructor() {
        this.diffCache = new Map();
    }

    /**
     * Genera un diff visual entre dos versiones de código
     */
    generateDiff(original, modified) {
        const originalLines = original.split('\n');
        const modifiedLines = modified.split('\n');
        
        // Algoritmo LCS simplificado para diff
        const diff = this.computeDiff(originalLines, modifiedLines);
        return diff;
    }

    computeDiff(oldLines, newLines) {
        const result = [];
        let oldIndex = 0;
        let newIndex = 0;
        
        // Matriz LCS
        const lcs = this.lcsMatrix(oldLines, newLines);
        
        // Backtrack para generar diff
        let i = oldLines.length;
        let j = newLines.length;
        const changes = [];
        
        while (i > 0 || j > 0) {
            if (i > 0 && j > 0 && oldLines[i-1] === newLines[j-1]) {
                changes.unshift({ type: 'unchanged', line: oldLines[i-1], oldNum: i, newNum: j });
                i--; j--;
            } else if (j > 0 && (i === 0 || lcs[i][j-1] >= lcs[i-1][j])) {
                changes.unshift({ type: 'added', line: newLines[j-1], newNum: j });
                j--;
            } else if (i > 0) {
                changes.unshift({ type: 'removed', line: oldLines[i-1], oldNum: i });
                i--;
            }
        }
        
        return changes;
    }

    lcsMatrix(a, b) {
        const m = a.length;
        const n = b.length;
        const matrix = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
        
        for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
                if (a[i-1] === b[j-1]) {
                    matrix[i][j] = matrix[i-1][j-1] + 1;
                } else {
                    matrix[i][j] = Math.max(matrix[i-1][j], matrix[i][j-1]);
                }
            }
        }
        
        return matrix;
    }

    /**
     * Renderiza el diff como HTML estilo GitHub
     */
    renderDiff(original, modified, options = {}) {
        const diff = this.generateDiff(original, modified);
        const { showLineNumbers = true, title = 'Cambios' } = options;
        
        let addedCount = 0;
        let removedCount = 0;
        
        let html = `
            <div class="diff-container" style="
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 13px;
                overflow: hidden;
            ">
                <div class="diff-header" style="
                    padding: 10px 16px;
                    background: #161b22;
                    border-bottom: 1px solid #30363d;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                ">
                    <span style="color: #c9d1d9; font-weight: 600;">📝 ${title}</span>
                    <span class="diff-stats" style="font-size: 12px;"></span>
                </div>
                <div class="diff-body" style="overflow-x: auto;">
        `;
        
        diff.forEach((change, idx) => {
            let bgColor, borderColor, symbol, textColor, numColor;
            
            switch (change.type) {
                case 'added':
                    bgColor = 'rgba(46, 160, 67, 0.15)';
                    borderColor = '#238636';
                    symbol = '+';
                    textColor = '#7ee787';
                    numColor = '#3fb950';
                    addedCount++;
                    break;
                case 'removed':
                    bgColor = 'rgba(248, 81, 73, 0.15)';
                    borderColor = '#f85149';
                    symbol = '-';
                    textColor = '#ffa198';
                    numColor = '#f85149';
                    removedCount++;
                    break;
                default:
                    bgColor = 'transparent';
                    borderColor = 'transparent';
                    symbol = ' ';
                    textColor = '#c9d1d9';
                    numColor = '#484f58';
            }
            
            const lineNum = change.oldNum || change.newNum || '';
            
            html += `
                <div class="diff-line" style="
                    display: flex;
                    background: ${bgColor};
                    border-left: 3px solid ${borderColor};
                ">
                    ${showLineNumbers ? `
                        <span style="
                            width: 50px;
                            padding: 0 8px;
                            text-align: right;
                            color: ${numColor};
                            background: rgba(0,0,0,0.1);
                            user-select: none;
                        ">${lineNum}</span>
                    ` : ''}
                    <span style="
                        width: 20px;
                        text-align: center;
                        color: ${textColor};
                        font-weight: bold;
                    ">${symbol}</span>
                    <pre style="
                        margin: 0;
                        padding: 0 8px;
                        color: ${textColor};
                        flex: 1;
                        white-space: pre-wrap;
                        word-break: break-all;
                    ">${this.escapeHtml(change.line)}</pre>
                </div>
            `;
        });
        
        html += '</div></div>';
        
        // Actualizar estadísticas
        const statsHtml = `
            <span style="color: #3fb950;">+${addedCount}</span>
            <span style="color: #484f58; margin: 0 4px;">/</span>
            <span style="color: #f85149;">-${removedCount}</span>
        `;
        
        // Insertar stats en el header
        html = html.replace('<span class="diff-stats" style="font-size: 12px;"></span>', 
                           `<span class="diff-stats" style="font-size: 12px;">${statsHtml}</span>`);
        
        return html;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Muestra el diff en un modal
     */
    showDiffModal(original, modified, title = 'Vista previa de cambios') {
        const diffHtml = this.renderDiff(original, modified, { title });
        
        const modal = document.createElement('div');
        modal.className = 'diff-modal-overlay';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100000;
        `;
        
        modal.innerHTML = `
            <div class="diff-modal" style="
                width: 90%;
                max-width: 900px;
                max-height: 80vh;
                background: #161b22;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            ">
                <div style="
                    padding: 16px 20px;
                    background: #21262d;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    border-bottom: 1px solid #30363d;
                ">
                    <span style="color: #c9d1d9; font-weight: 600; font-size: 16px;">
                        🔍 ${title}
                    </span>
                    <button onclick="this.closest('.diff-modal-overlay').remove()" style="
                        background: #30363d;
                        border: none;
                        color: #c9d1d9;
                        padding: 6px 12px;
                        border-radius: 6px;
                        cursor: pointer;
                    ">✕ Cerrar</button>
                </div>
                <div style="padding: 16px; max-height: calc(80vh - 80px); overflow-y: auto;">
                    ${diffHtml}
                </div>
                <div style="
                    padding: 12px 20px;
                    background: #21262d;
                    border-top: 1px solid #30363d;
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                ">
                    <button onclick="this.closest('.diff-modal-overlay').remove()" style="
                        background: #30363d;
                        border: none;
                        color: #c9d1d9;
                        padding: 8px 16px;
                        border-radius: 6px;
                        cursor: pointer;
                    ">Cancelar</button>
                    <button onclick="window.diffPreview.applyChanges(); this.closest('.diff-modal-overlay').remove()" style="
                        background: #238636;
                        border: none;
                        color: white;
                        padding: 8px 16px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 500;
                    ">✓ Aplicar cambios</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Cerrar con Escape
        const closeOnEscape = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', closeOnEscape);
            }
        };
        document.addEventListener('keydown', closeOnEscape);
    }

    applyChanges() {
        // Callback para aplicar cambios (se puede sobrescribir)
        console.log('Cambios aplicados');
    }
}

// Instancia global
window.diffPreview = new DiffPreview();
console.log('✅ DiffPreview inicializado');
