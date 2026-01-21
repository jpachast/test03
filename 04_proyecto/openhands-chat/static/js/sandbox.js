/**
 * Sandbox de Ejecución de Código - UI JavaScript
 * Permite ejecutar código Python, JavaScript, Bash desde el chat
 */

class CodeSandbox {
    constructor() {
        this.currentLanguage = 'python';
        this.executionHistory = [];
        this.isExecuting = false;
    }

    /**
     * Inicializa el sandbox
     */
    async init() {
        await this.loadLanguages();
        this.setupEventListeners();
    }

    /**
     * Carga los lenguajes soportados
     */
    async loadLanguages() {
        try {
            const response = await fetch('/api/sandbox/languages');
            const data = await response.json();
            this.supportedLanguages = data.languages;
        } catch (error) {
            console.error('Error cargando lenguajes:', error);
            this.supportedLanguages = {
                'python': 'Python 3.x',
                'javascript': 'Node.js',
                'bash': 'Bash Shell'
            };
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Detectar bloques de código en el chat y añadir botón de ejecutar
        this.observeChatMessages();
    }

    /**
     * Observa nuevos mensajes del chat para añadir botones de ejecutar
     */
    observeChatMessages() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        this.addExecuteButtons(node);
                    }
                });
            });
        });

        // Observar el contenedor de mensajes
        const chatContainer = document.querySelector('.chat-messages, #chat-messages, .messages-container');
        if (chatContainer) {
            observer.observe(chatContainer, { childList: true, subtree: true });
        }

        // También procesar mensajes existentes
        document.querySelectorAll('pre code').forEach(block => {
            this.addExecuteButtonToBlock(block);
        });
    }

    /**
     * Añade botones de ejecutar a bloques de código
     */
    addExecuteButtons(container) {
        const codeBlocks = container.querySelectorAll ? 
            container.querySelectorAll('pre code') : [];
        
        codeBlocks.forEach(block => {
            this.addExecuteButtonToBlock(block);
        });
    }

    /**
     * Añade botón de ejecutar a un bloque de código específico
     */
    addExecuteButtonToBlock(codeBlock) {
        // Evitar duplicados
        if (codeBlock.dataset.sandboxEnabled) return;
        codeBlock.dataset.sandboxEnabled = 'true';

        const pre = codeBlock.parentElement;
        if (!pre || pre.tagName !== 'PRE') return;

        // Detectar lenguaje
        const language = this.detectLanguageFromBlock(codeBlock);
        
        // Solo añadir si es un lenguaje ejecutable
        if (!['python', 'javascript', 'js', 'bash', 'shell', 'sh', 'typescript', 'ts'].includes(language)) {
            return;
        }

        // Crear contenedor de botones
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'sandbox-buttons';
        buttonContainer.style.cssText = `
            position: absolute;
            top: 5px;
            right: 5px;
            display: flex;
            gap: 5px;
            z-index: 10;
        `;

        // Botón de ejecutar
        const runBtn = document.createElement('button');
        runBtn.innerHTML = '▶️ Ejecutar';
        runBtn.className = 'sandbox-run-btn';
        runBtn.style.cssText = `
            background: #22c55e;
            color: white;
            border: none;
            padding: 4px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
        `;
        runBtn.onclick = () => this.executeCodeBlock(codeBlock, language);

        // Botón de copiar
        const copyBtn = document.createElement('button');
        copyBtn.innerHTML = '📋';
        copyBtn.className = 'sandbox-copy-btn';
        copyBtn.style.cssText = `
            background: #3b82f6;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        `;
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(codeBlock.textContent);
            copyBtn.innerHTML = '✓';
            setTimeout(() => copyBtn.innerHTML = '📋', 1500);
        };

        buttonContainer.appendChild(runBtn);
        buttonContainer.appendChild(copyBtn);

        // Hacer el pre relativo para posicionar los botones
        pre.style.position = 'relative';
        pre.appendChild(buttonContainer);
    }

    /**
     * Detecta el lenguaje de un bloque de código
     */
    detectLanguageFromBlock(codeBlock) {
        // Intentar desde la clase
        const classes = codeBlock.className.split(' ');
        for (const cls of classes) {
            if (cls.startsWith('language-')) {
                return cls.replace('language-', '').toLowerCase();
            }
            if (cls.startsWith('lang-')) {
                return cls.replace('lang-', '').toLowerCase();
            }
        }
        
        // Detectar por contenido
        const code = codeBlock.textContent;
        return this.detectLanguage(code);
    }

    /**
     * Detecta el lenguaje por el contenido del código
     */
    detectLanguage(code) {
        const lower = code.toLowerCase();
        
        // Python patterns
        if (/\bdef\s+\w+\s*\(/.test(code) || /\bimport\s+\w+/.test(code) || 
            /\bprint\s*\(/.test(code) || /\bclass\s+\w+/.test(code)) {
            return 'python';
        }
        
        // JavaScript patterns
        if (/\bconst\s+\w+/.test(code) || /\blet\s+\w+/.test(code) ||
            /\bconsole\.log/.test(code) || /\bfunction\s+\w+/.test(code)) {
            return 'javascript';
        }
        
        // Bash patterns
        if (/\becho\s+/.test(code) || /\$\{?\w+\}?/.test(code) ||
            /\bif\s+\[\s*/.test(code) || code.startsWith('#!/bin/bash')) {
            return 'bash';
        }
        
        return 'python'; // Default
    }

    /**
     * Ejecuta un bloque de código
     */
    async executeCodeBlock(codeBlock, language) {
        const code = codeBlock.textContent;
        const result = await this.execute(code, language);
        this.showResult(result, codeBlock.parentElement);
    }

    /**
     * Ejecuta código en el sandbox
     */
    async execute(code, language = null, timeout = null) {
        if (this.isExecuting) {
            return { status: 'error', stderr: 'Ya hay una ejecución en curso' };
        }

        this.isExecuting = true;

        try {
            const response = await fetch('/api/sandbox/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language, timeout })
            });

            const result = await response.json();
            this.executionHistory.unshift(result);
            
            // Mantener solo últimas 50 ejecuciones en memoria
            if (this.executionHistory.length > 50) {
                this.executionHistory.pop();
            }

            return result;
        } catch (error) {
            return {
                status: 'error',
                stderr: `Error de conexión: ${error.message}`,
                exit_code: 1
            };
        } finally {
            this.isExecuting = false;
        }
    }

    /**
     * Muestra el resultado de una ejecución
     */
    showResult(result, codeBlockContainer) {
        // Remover resultado anterior si existe
        const existingResult = codeBlockContainer.querySelector('.sandbox-result');
        if (existingResult) {
            existingResult.remove();
        }

        // Crear contenedor de resultado
        const resultDiv = document.createElement('div');
        resultDiv.className = 'sandbox-result';
        
        const isSuccess = result.status === 'success';
        const wasAutoFixed = result.auto_fixed === true;
        
        // Si fue auto-fixed, mostrar color especial (azul/cyan)
        let statusColor = isSuccess ? '#22c55e' : '#ef4444';
        let statusIcon = isSuccess ? '✅' : '❌';
        let statusText = this.getStatusText(result.status);
        
        if (wasAutoFixed) {
            statusColor = '#06b6d4'; // Cyan para auto-fix
            statusIcon = '🔧';
            statusText = `Auto-Fix aplicado (${result.fix_iterations} iteraciones)`;
        }

        resultDiv.innerHTML = `
            <div style="
                background: #1e1e1e;
                border: 1px solid ${statusColor};
                border-radius: 8px;
                margin-top: 10px;
                overflow: hidden;
            ">
                <div style="
                    background: ${statusColor}22;
                    padding: 8px 12px;
                    border-bottom: 1px solid ${statusColor}44;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <span style="color: ${statusColor}; font-weight: bold;">
                        ${statusIcon} ${statusText}
                    </span>
                    <span style="color: #888; font-size: 12px;">
                        ${result.language || 'auto'} • ${result.execution_time || 0}s
                    </span>
                </div>
                
                ${wasAutoFixed ? `
                    <div style="padding: 12px;">
                        <div style="
                            background: #083344;
                            border: 1px solid #06b6d4;
                            border-radius: 4px;
                            padding: 10px;
                            color: #67e8f9;
                            font-size: 13px;
                        ">
                            <strong>🔧 Auto-Fix:</strong> ${result.fix_applied || 'Corrección aplicada automáticamente'}
                            <br><span style="color: #a5f3fc; font-size: 11px;">El código tenía un error que fue corregido y re-ejecutado automáticamente.</span>
                        </div>
                    </div>
                ` : ''}
                
                ${result.stdout ? `
                    <div style="padding: 12px; padding-top: ${wasAutoFixed ? '0' : '12px'};">
                        <div style="color: #22c55e; font-size: 11px; margin-bottom: 4px;">📤 Output:</div>
                        <pre style="
                            background: #0d0d0d;
                            padding: 10px;
                            border-radius: 4px;
                            margin: 0;
                            overflow-x: auto;
                            color: #e5e5e5;
                            font-size: 13px;
                        ">${this.escapeHtml(result.stdout)}</pre>
                    </div>
                ` : ''}
                
                ${result.stderr ? `
                    <div style="padding: 12px; padding-top: ${result.stdout ? '0' : '12px'};">
                        <div style="color: #ef4444; font-size: 11px; margin-bottom: 4px;">⚠️ Error:</div>
                        <pre style="
                            background: #1a0000;
                            padding: 10px;
                            border-radius: 4px;
                            margin: 0;
                            overflow-x: auto;
                            color: #fca5a5;
                            font-size: 13px;
                        ">${this.escapeHtml(result.stderr)}</pre>
                    </div>
                ` : ''}
                
                ${result.error_analysis && !wasAutoFixed ? `
                    <div style="padding: 12px; padding-top: 0;">
                        <div style="
                            background: #fef3c7;
                            border: 1px solid #f59e0b;
                            border-radius: 4px;
                            padding: 10px;
                            color: #92400e;
                            font-size: 13px;
                        ">
                            <strong>🔍 Análisis:</strong> ${result.error_analysis}
                            ${result.suggested_fix ? `<br><strong>💡 Sugerencia:</strong> <code>${result.suggested_fix}</code>` : ''}
                        </div>
                    </div>
                ` : ''}
                
                ${!result.stdout && !result.stderr && !wasAutoFixed ? `
                    <div style="padding: 12px; color: #888; font-style: italic;">
                        (Sin output)
                    </div>
                ` : ''}
            </div>
        `;

        codeBlockContainer.appendChild(resultDiv);

        // Scroll al resultado
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Obtiene el texto del estado
     */
    getStatusText(status) {
        const texts = {
            'success': 'Ejecución exitosa',
            'error': 'Error en la ejecución',
            'timeout': 'Tiempo agotado',
            'cancelled': 'Cancelado',
            'running': 'Ejecutando...',
            'pending': 'Pendiente'
        };
        return texts[status] || status;
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Abre el modal del sandbox
     */
    openModal() {
        // Cerrar otros modales
        document.querySelectorAll('.modal-overlay').forEach(m => m.remove());

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 800px; max-height: 90vh;">
                <div class="modal-header">
                    <h3>🖥️ Sandbox de Código</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body" style="display: flex; flex-direction: column; gap: 15px;">
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <label style="color: #888;">Lenguaje:</label>
                        <select id="sandbox-language" style="
                            background: #2d2d2d;
                            border: 1px solid #444;
                            color: white;
                            padding: 8px 12px;
                            border-radius: 6px;
                        ">
                            <option value="python">🐍 Python</option>
                            <option value="javascript">📜 JavaScript</option>
                            <option value="bash">💻 Bash</option>
                            <option value="typescript">📘 TypeScript</option>
                        </select>
                        <button onclick="codeSandbox.executeFromModal()" style="
                            background: #22c55e;
                            color: white;
                            border: none;
                            padding: 8px 20px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-weight: bold;
                        ">▶️ Ejecutar</button>
                    </div>
                    
                    <div>
                        <label style="color: #888; display: block; margin-bottom: 5px;">Código:</label>
                        <textarea id="sandbox-code" placeholder="Escribe tu código aquí..." style="
                            width: 100%;
                            height: 200px;
                            background: #1e1e1e;
                            border: 1px solid #444;
                            color: #e5e5e5;
                            padding: 12px;
                            border-radius: 6px;
                            font-family: 'Monaco', 'Menlo', monospace;
                            font-size: 14px;
                            resize: vertical;
                        ">print("Hello, World!")
for i in range(5):
    print(f"Número: {i}")</textarea>
                    </div>
                    
                    <div id="sandbox-result-container"></div>
                    
                    <div style="border-top: 1px solid #333; padding-top: 15px;">
                        <h4 style="color: #888; margin-bottom: 10px;">📜 Historial de Ejecuciones</h4>
                        <div id="sandbox-history" style="max-height: 150px; overflow-y: auto;"></div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };

        this.updateHistoryView();
    }

    /**
     * Ejecuta código desde el modal
     */
    async executeFromModal() {
        const code = document.getElementById('sandbox-code').value;
        const language = document.getElementById('sandbox-language').value;
        const resultContainer = document.getElementById('sandbox-result-container');

        if (!code.trim()) {
            resultContainer.innerHTML = '<div style="color: #f59e0b;">⚠️ Escribe algo de código primero</div>';
            return;
        }

        resultContainer.innerHTML = '<div style="color: #3b82f6;">⏳ Ejecutando...</div>';

        const result = await this.execute(code, language);

        const isSuccess = result.status === 'success';
        const statusColor = isSuccess ? '#22c55e' : '#ef4444';

        resultContainer.innerHTML = `
            <div style="
                background: #1e1e1e;
                border: 1px solid ${statusColor};
                border-radius: 8px;
                overflow: hidden;
            ">
                <div style="
                    background: ${statusColor}22;
                    padding: 8px 12px;
                    display: flex;
                    justify-content: space-between;
                ">
                    <span style="color: ${statusColor}; font-weight: bold;">
                        ${isSuccess ? '✅' : '❌'} ${this.getStatusText(result.status)}
                    </span>
                    <span style="color: #888; font-size: 12px;">
                        Exit: ${result.exit_code} • ${result.execution_time}s
                    </span>
                </div>
                ${result.stdout ? `
                    <div style="padding: 12px;">
                        <pre style="
                            background: #0d0d0d;
                            padding: 10px;
                            border-radius: 4px;
                            margin: 0;
                            color: #e5e5e5;
                            overflow-x: auto;
                        ">${this.escapeHtml(result.stdout)}</pre>
                    </div>
                ` : ''}
                ${result.stderr ? `
                    <div style="padding: 12px; padding-top: 0;">
                        <pre style="
                            background: #1a0000;
                            padding: 10px;
                            border-radius: 4px;
                            margin: 0;
                            color: #fca5a5;
                            overflow-x: auto;
                        ">${this.escapeHtml(result.stderr)}</pre>
                    </div>
                ` : ''}
                ${result.error_analysis ? `
                    <div style="padding: 12px; padding-top: 0;">
                        <div style="
                            background: #fef3c7;
                            padding: 10px;
                            border-radius: 4px;
                            color: #92400e;
                        ">
                            🔍 ${result.error_analysis}
                            ${result.suggested_fix ? `<br>💡 <code>${result.suggested_fix}</code>` : ''}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        this.updateHistoryView();
    }

    /**
     * Actualiza la vista del historial
     */
    updateHistoryView() {
        const container = document.getElementById('sandbox-history');
        if (!container) return;

        if (this.executionHistory.length === 0) {
            container.innerHTML = '<div style="color: #666; font-style: italic;">Sin ejecuciones aún</div>';
            return;
        }

        container.innerHTML = this.executionHistory.slice(0, 10).map(exec => `
            <div style="
                background: #2d2d2d;
                padding: 8px 12px;
                border-radius: 4px;
                margin-bottom: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 13px;
            ">
                <span>
                    ${exec.status === 'success' ? '✅' : '❌'}
                    <code style="color: #888;">${exec.language}</code>
                    ${exec.code ? exec.code.substring(0, 30) + '...' : ''}
                </span>
                <span style="color: #666;">${exec.execution_time}s</span>
            </div>
        `).join('');
    }
}

// Instancia global
const codeSandbox = new CodeSandbox();

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    codeSandbox.init();
});

// Función global para abrir el modal desde el menú
function openSandboxModal() {
    codeSandbox.openModal();
}
