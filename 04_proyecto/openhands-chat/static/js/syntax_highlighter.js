/**
 * Syntax Highlighting Profesional - FIX REAL
 * Aplica highlight.js a todos los bloques de código
 */

class SyntaxHighlighter {
    constructor() {
        this.initialized = false;
        this.observer = null;
        this.highlightQueue = [];
        this.isProcessing = false;
        this.init();
    }

    init() {
        // Esperar a que highlight.js esté disponible
        if (typeof hljs === 'undefined') {
            console.log('[SyntaxHighlighter] Esperando hljs...');
            setTimeout(() => this.init(), 100);
            return;
        }

        // Configurar highlight.js
        hljs.configure({
            ignoreUnescapedHTML: true,
            languages: ['python', 'javascript', 'bash', 'typescript', 'json', 'css', 'xml', 'html', 'shell']
        });

        // Aplicar a código existente
        this.highlightAll();

        // Observar nuevos elementos - CORREGIDO
        this.observeNewCode();

        // También ejecutar periódicamente para bloques que se escapan
        setInterval(() => this.highlightAll(), 2000);

        this.initialized = true;
        console.log('✅ SyntaxHighlighter inicializado correctamente');
    }

    highlightAll() {
        const blocks = document.querySelectorAll('pre code:not(.hljs)');
        if (blocks.length > 0) {
            console.log(`[SyntaxHighlighter] Encontrados ${blocks.length} bloques sin highlight`);
            blocks.forEach((block) => this.highlightBlock(block));
        }
    }

    highlightBlock(block) {
        if (block.classList.contains('hljs')) return;
        
        try {
            // Detectar lenguaje de la clase
            let lang = null;
            const classes = block.className.split(' ');
            for (const cls of classes) {
                if (cls.startsWith('language-') || cls.startsWith('lang-')) {
                    lang = cls.replace('language-', '').replace('lang-', '');
                    break;
                }
            }

            // Si no hay lenguaje, detectarlo
            if (!lang || lang === '') {
                lang = this.detectLanguage(block.textContent);
                if (lang) {
                    block.classList.add(`language-${lang}`);
                }
            }

            // Aplicar highlight
            hljs.highlightElement(block);
            
            // Añadir estilos al pre padre
            const pre = block.parentElement;
            if (pre && pre.tagName === 'PRE') {
                pre.style.borderRadius = '8px';
                pre.style.padding = '12px';
                pre.style.margin = '8px 0';
                pre.style.overflow = 'auto';
            }

            console.log(`[SyntaxHighlighter] ✓ Highlighted: ${lang || 'auto'}`);
        } catch (e) {
            console.error('[SyntaxHighlighter] Error:', e);
        }
    }

    detectLanguage(code) {
        if (!code) return 'plaintext';
        
        // Python
        if (code.includes('def ') || code.includes('import ') || 
            code.includes('print(') || code.includes('class ') && code.includes('self')) {
            return 'python';
        }
        // JavaScript/TypeScript
        if (code.includes('console.log') || code.includes('const ') || 
            code.includes('let ') || code.includes('=>') || code.includes('function ')) {
            return code.includes(': string') || code.includes(': number') ? 'typescript' : 'javascript';
        }
        // Bash/Shell
        if (code.includes('#!/bin/bash') || code.includes('echo ') || 
            code.match(/^\s*(cd|ls|mkdir|rm|cp|mv|cat|grep|npm|pip|python|node)\s/m)) {
            return 'bash';
        }
        // JSON
        if ((code.trim().startsWith('{') && code.trim().endsWith('}')) ||
            (code.trim().startsWith('[') && code.trim().endsWith(']'))) {
            return 'json';
        }
        // HTML
        if (code.includes('</') && code.includes('>')) {
            return 'html';
        }
        return 'plaintext';
    }

    observeNewCode() {
        if (this.observer) return;

        this.observer = new MutationObserver((mutations) => {
            let shouldHighlight = false;
            
            mutations.forEach((mutation) => {
                // Verificar nodos añadidos
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        // Buscar bloques de código
                        if (node.matches && node.matches('pre code:not(.hljs)')) {
                            this.highlightBlock(node);
                            shouldHighlight = true;
                        }
                        
                        const codeBlocks = node.querySelectorAll ? 
                            node.querySelectorAll('pre code:not(.hljs)') : [];
                        if (codeBlocks.length > 0) {
                            codeBlocks.forEach((block) => this.highlightBlock(block));
                            shouldHighlight = true;
                        }
                    }
                });

                // También verificar cambios en innerHTML (characterData)
                if (mutation.type === 'characterData' || mutation.type === 'childList') {
                    shouldHighlight = true;
                }
            });

            // Si hubo cambios, hacer highlight después de un pequeño delay
            if (shouldHighlight) {
                clearTimeout(this.highlightTimeout);
                this.highlightTimeout = setTimeout(() => this.highlightAll(), 100);
            }
        });

        // Observar todo el documento
        this.observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });

        console.log('[SyntaxHighlighter] Observer activado');
    }
}

// Inicializar inmediatamente
let syntaxHighlighter;

function initSyntaxHighlighter() {
    if (typeof hljs !== 'undefined') {
        syntaxHighlighter = new SyntaxHighlighter();
        window.syntaxHighlighter = syntaxHighlighter;
    } else {
        setTimeout(initSyntaxHighlighter, 100);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSyntaxHighlighter);
} else {
    initSyntaxHighlighter();
}

// También exponer función global para forzar highlight
window.highlightAllCode = function() {
    if (window.syntaxHighlighter) {
        window.syntaxHighlighter.highlightAll();
    } else if (typeof hljs !== 'undefined') {
        document.querySelectorAll('pre code:not(.hljs)').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
};

window.SyntaxHighlighter = SyntaxHighlighter;
