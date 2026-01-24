/**
 * Chat Sandbox Integration - Ejecución automática de código en el chat
 * Nivel profesional: como Cursor, Devin, Windsurf
 */

class ChatSandboxIntegration {
    constructor() {
        this.autoExecute = true;
        this.executionResults = new Map();
        this.init();
    }

    init() {
        // Observar nuevos mensajes del agente
        this.observeMessages();
        console.log('🚀 Chat Sandbox Integration inicializado');
    }

    observeMessages() {
        // Observar cambios en el contenedor de mensajes
        const chatContainer = document.querySelector('.chat-messages, .messages-container, #chat-messages');
        if (!chatContainer) {
            setTimeout(() => this.observeMessages(), 1000);
            return;
        }

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.classList?.contains('message')) {
                        this.processMessage(node);
                    }
                });
            });
        });

        observer.observe(chatContainer, { childList: true, subtree: true });
    }

    processMessage(messageElement) {
        // Buscar bloques de código en el mensaje
        const codeBlocks = messageElement.querySelectorAll('pre code, .code-block');
        
        codeBlocks.forEach((block, index) => {
            if (block.dataset.sandboxProcessed) return;
            block.dataset.sandboxProcessed = 'true';
            
            const language = this.detectLanguage(block);
            const code = block.textContent;
            
            if (this.isExecutableCode(language, code)) {
                this.addExecutionUI(block, code, language, index);
            }
        });
    }

    detectLanguage(block) {
        // Detectar lenguaje por clase
        const classes = block.className || '';
        if (classes.includes('python') || classes.includes('py')) return 'python';
        if (classes.includes('javascript') || classes.includes('js')) return 'javascript';
        if (classes.includes('bash') || classes.includes('shell') || classes.includes('sh')) return 'bash';
        if (classes.includes('typescript') || classes.includes('ts')) return 'typescript';
        
        // Detectar por contenido
        const code = block.textContent;
        if (code.includes('def ') || code.includes('import ') || code.includes('print(')) return 'python';
        if (code.includes('console.log') || code.includes('const ') || code.includes('let ')) return 'javascript';
        if (code.includes('#!/bin/bash') || code.includes('echo ') || code.includes('cd ')) return 'bash';
        
        return 'python'; // default
    }

    isExecutableCode(language, code) {
        // No ejecutar código muy corto o que sea solo comentarios
        const lines = code.trim().split('\n').filter(l => l.trim() && !l.trim().startsWith('#') && !l.trim().startsWith('//'));
        return lines.length > 0 && ['python', 'javascript', 'bash', 'typescript'].includes(language);
    }

    addExecutionUI(codeBlock, code, language, index) {
        // Crear contenedor para la UI de ejecución
        const container = document.createElement('div');
        container.className = 'sandbox-execution-container';
        container.innerHTML = `
            <div class="sandbox-toolbar" style="
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-radius: 8px 8px 0 0;
                border-bottom: 1px solid #333;
            ">
                <span class="sandbox-lang" style="
                    background: ${this.getLangColor(language)};
                    color: white;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                    text-transform: uppercase;
                ">${language}</span>
                <button class="sandbox-run-btn" style="
                    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                    color: white;
                    border: none;
                    padding: 6px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    transition: all 0.2s;
                ">
                    <span>▶</span> Ejecutar
                </button>
                <button class="sandbox-copy-btn" style="
                    background: #374151;
                    color: #9ca3af;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 12px;
                ">📋 Copiar</button>
                <span class="sandbox-status" style="
                    margin-left: auto;
                    font-size: 11px;
                    color: #6b7280;
                "></span>
            </div>
            <div class="sandbox-result" style="
                display: none;
                background: #0d1117;
                border-radius: 0 0 8px 8px;
                overflow: hidden;
            "></div>
        `;

        // Insertar antes del bloque de código
        codeBlock.parentElement.insertBefore(container, codeBlock);
        codeBlock.style.borderRadius = '0';
        codeBlock.style.marginTop = '0';

        // Event listeners
        const runBtn = container.querySelector('.sandbox-run-btn');
        const copyBtn = container.querySelector('.sandbox-copy-btn');
        const statusEl = container.querySelector('.sandbox-status');
        const resultEl = container.querySelector('.sandbox-result');

        runBtn.addEventListener('click', () => this.executeCode(code, language, resultEl, statusEl, runBtn));
        copyBtn.addEventListener('click', () => this.copyCode(code, copyBtn));

        // Auto-ejecutar si está habilitado
        if (this.autoExecute && this.shouldAutoExecute(code, language)) {
            setTimeout(() => this.executeCode(code, language, resultEl, statusEl, runBtn), 500);
        }
    }

    getLangColor(language) {
        const colors = {
            python: '#3776ab',
            javascript: '#f7df1e',
            bash: '#4eaa25',
            typescript: '#3178c6'
        };
        return colors[language] || '#6b7280';
    }

    shouldAutoExecute(code, language) {
        // No auto-ejecutar código peligroso
        const dangerousPatterns = [
            'rm -rf', 'sudo', 'chmod', 'chown', 
            'DROP TABLE', 'DELETE FROM',
            'os.system', 'subprocess.call',
            'eval(', 'exec('
        ];
        return !dangerousPatterns.some(p => code.includes(p));
    }

    async executeCode(code, language, resultEl, statusEl, runBtn) {
        // Mostrar estado de ejecución
        runBtn.disabled = true;
        runBtn.innerHTML = '<span class="spinner">⏳</span> Ejecutando...';
        statusEl.textContent = 'Ejecutando en el proyecto...';
        statusEl.style.color = '#fbbf24';

        try {
            const response = await fetch('/api/sandbox-chat/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language, auto_fix: false })
            });

            const data = await response.json();
            this.showResult(data, resultEl, statusEl, runBtn, code, language);

        } catch (error) {
            this.showError(error.message, resultEl, statusEl, runBtn);
        }
    }

    showResult(data, resultEl, statusEl, runBtn, code, language) {
        resultEl.style.display = 'block';
        const result = data.result || data;
        const success = data.success || result.success;

        if (success) {
            statusEl.textContent = `✓ Ejecutado en ${result.execution_time || '< 1'}s`;
            statusEl.style.color = '#22c55e';
            runBtn.innerHTML = '<span>▶</span> Ejecutar';
            runBtn.disabled = false;

            resultEl.innerHTML = `
                <div style="padding: 12px;">
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin-bottom: 8px;
                        color: #22c55e;
                        font-weight: bold;
                        font-size: 13px;
                    ">
                        <span>✅</span> Salida
                    </div>
                    <pre style="
                        background: #161b22;
                        padding: 12px;
                        border-radius: 6px;
                        margin: 0;
                        overflow-x: auto;
                        font-family: 'Monaco', 'Menlo', monospace;
                        font-size: 13px;
                        color: #c9d1d9;
                        white-space: pre-wrap;
                        max-height: 300px;
                        overflow-y: auto;
                    ">${this.escapeHtml(result.stdout || '(sin salida)')}</pre>
                </div>
            `;
        } else {
            statusEl.textContent = '✗ Error detectado';
            statusEl.style.color = '#ef4444';
            runBtn.innerHTML = '<span>▶</span> Reintentar';
            runBtn.disabled = false;

            const errorType = result.error_type || 'Error';
            const suggestedFix = result.suggested_fix;

            resultEl.innerHTML = `
                <div style="padding: 12px;">
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin-bottom: 8px;
                        color: #ef4444;
                        font-weight: bold;
                        font-size: 13px;
                    ">
                        <span>❌</span> ${errorType}
                    </div>
                    <pre style="
                        background: #2d1f1f;
                        padding: 12px;
                        border-radius: 6px;
                        margin: 0;
                        overflow-x: auto;
                        font-family: 'Monaco', 'Menlo', monospace;
                        font-size: 12px;
                        color: #fca5a5;
                        white-space: pre-wrap;
                        max-height: 200px;
                        overflow-y: auto;
                        border-left: 3px solid #ef4444;
                    ">${this.escapeHtml(result.stderr || 'Error desconocido')}</pre>
                    ${suggestedFix ? `
                        <div style="
                            margin-top: 12px;
                            padding: 12px;
                            background: #1e293b;
                            border-radius: 6px;
                            border-left: 3px solid #3b82f6;
                        ">
                            <div style="
                                color: #60a5fa;
                                font-weight: bold;
                                font-size: 12px;
                                margin-bottom: 6px;
                            ">💡 Sugerencia de corrección:</div>
                            <div style="color: #94a3b8; font-size: 13px;">${this.escapeHtml(suggestedFix)}</div>
                            <button class="apply-fix-btn" style="
                                margin-top: 10px;
                                background: #3b82f6;
                                color: white;
                                border: none;
                                padding: 6px 14px;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 12px;
                            ">🔧 Aplicar corrección</button>
                        </div>
                    ` : ''}
                </div>
            `;

            // Event para aplicar corrección
            const applyBtn = resultEl.querySelector('.apply-fix-btn');
            if (applyBtn) {
                applyBtn.addEventListener('click', () => this.applyFix(code, language, suggestedFix, resultEl, statusEl, runBtn));
            }
        }
    }

    showError(message, resultEl, statusEl, runBtn) {
        statusEl.textContent = '✗ Error de conexión';
        statusEl.style.color = '#ef4444';
        runBtn.innerHTML = '<span>▶</span> Reintentar';
        runBtn.disabled = false;

        resultEl.style.display = 'block';
        resultEl.innerHTML = `
            <div style="padding: 12px; color: #ef4444;">
                <strong>Error:</strong> ${this.escapeHtml(message)}
            </div>
        `;
    }

    async applyFix(originalCode, language, suggestion, resultEl, statusEl, runBtn) {
        // Aquí se podría integrar con el LLM para aplicar la corrección
        // Por ahora mostramos un mensaje
        statusEl.textContent = 'Aplicando corrección...';
        statusEl.style.color = '#fbbf24';
        
        // TODO: Integrar con el agente para aplicar el fix automáticamente
        alert(`Sugerencia: ${suggestion}\n\nPuedes copiar esta sugerencia y pedirle al agente que la aplique.`);
    }

    copyCode(code, btn) {
        navigator.clipboard.writeText(code).then(() => {
            const originalText = btn.textContent;
            btn.textContent = '✓ Copiado';
            btn.style.color = '#22c55e';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.color = '#9ca3af';
            }, 2000);
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // API pública para ejecutar código programáticamente
    async execute(code, language = 'python') {
        try {
            const response = await fetch('/api/sandbox-chat/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language })
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Toggle auto-ejecución
    setAutoExecute(enabled) {
        this.autoExecute = enabled;
        console.log(`Auto-ejecución ${enabled ? 'activada' : 'desactivada'}`);
    }
}

// También procesar mensajes existentes cuando se carga
function processExistingMessages() {
    document.querySelectorAll('pre code, .code-block').forEach((block, index) => {
        if (!block.dataset.sandboxProcessed) {
            window.chatSandbox?.processMessage(block.closest('.message') || block.parentElement);
        }
    });
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.chatSandbox = new ChatSandboxIntegration();
        setTimeout(processExistingMessages, 1000);
    });
} else {
    window.chatSandbox = new ChatSandboxIntegration();
    setTimeout(processExistingMessages, 1000);
}

// Exportar para uso global
window.ChatSandboxIntegration = ChatSandboxIntegration;
