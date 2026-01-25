/**
 * UI Polish Module - Pulido profesional de la interfaz
 * Mejora visual de mensajes, animaciones y experiencia de usuario
 */
(function() {
    'use strict';
    
    // Configuración
    const config = {
        enableAnimations: true,
        enableGlowEffects: true,
        enableSmoothScroll: true,
        messageDelay: 50  // ms entre caracteres para efecto typing
    };
    
    // Inyectar estilos profesionales
    function injectStyles() {
        if (document.getElementById('ui-polish-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'ui-polish-styles';
        styles.textContent = `
            /* ===== VARIABLES GLOBALES ===== */
            :root {
                --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                --warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                --dark-bg: #0d1117;
                --card-bg: #161b22;
                --border-color: #30363d;
                --text-primary: #e6edf3;
                --text-secondary: #8b949e;
                --accent-blue: #58a6ff;
                --accent-green: #3fb950;
                --accent-purple: #a371f7;
                --shadow-glow: 0 0 20px rgba(88, 166, 255, 0.15);
            }
            
            /* ===== MENSAJES DEL CHAT ===== */
            .message {
                position: relative;
                padding: 16px 20px;
                margin: 12px 0;
                border-radius: 16px;
                animation: messageSlideIn 0.3s ease-out;
                transition: all 0.2s ease;
            }
            
            @keyframes messageSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            /* Mensaje del usuario */
            .message.user {
                background: var(--primary-gradient);
                color: white;
                margin-left: 15%;
                border-bottom-right-radius: 4px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .message.user::after {
                content: '';
                position: absolute;
                bottom: 0;
                right: -8px;
                width: 0;
                height: 0;
                border: 8px solid transparent;
                border-left-color: #764ba2;
                border-bottom: 0;
            }
            
            /* Mensaje del asistente */
            .message.assistant {
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                margin-right: 10%;
                border-bottom-left-radius: 4px;
                box-shadow: var(--shadow-glow);
            }
            
            .message.assistant::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: var(--primary-gradient);
                border-radius: 16px 16px 0 0;
                opacity: 0.8;
            }
            
            .message.assistant:hover {
                border-color: var(--accent-blue);
                box-shadow: 0 0 25px rgba(88, 166, 255, 0.2);
            }
            
            /* Mensaje del sistema */
            .message.system {
                background: linear-gradient(135deg, rgba(63, 185, 80, 0.1) 0%, rgba(17, 153, 142, 0.1) 100%);
                border: 1px solid rgba(63, 185, 80, 0.3);
                text-align: center;
                color: var(--accent-green);
                font-size: 14px;
            }
            
            /* ===== BLOQUES DE CÓDIGO ===== */
            .message pre {
                background: #0d1117 !important;
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 16px;
                margin: 12px 0;
                overflow-x: auto;
                position: relative;
                box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.3);
            }
            
            .message pre::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 32px;
                background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, transparent 100%);
                border-radius: 12px 12px 0 0;
                pointer-events: none;
            }
            
            .message code {
                font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
                font-size: 13px;
                line-height: 1.6;
            }
            
            .message p code {
                background: rgba(110, 118, 129, 0.2);
                padding: 2px 6px;
                border-radius: 4px;
                color: var(--accent-purple);
                font-size: 0.9em;
            }
            
            /* ===== LISTAS ===== */
            .message ul, .message ol {
                padding-left: 24px;
                margin: 10px 0;
            }
            
            .message li {
                margin: 8px 0;
                position: relative;
            }
            
            .message ul li::marker {
                color: var(--accent-blue);
            }
            
            /* ===== ENCABEZADOS ===== */
            .message h1, .message h2, .message h3, .message h4 {
                margin: 16px 0 12px 0;
                padding-bottom: 8px;
                border-bottom: 1px solid var(--border-color);
                color: var(--text-primary);
            }
            
            .message h1 { font-size: 1.5em; }
            .message h2 { font-size: 1.3em; }
            .message h3 { font-size: 1.15em; }
            
            /* ===== ENLACES ===== */
            .message a {
                color: var(--accent-blue);
                text-decoration: none;
                border-bottom: 1px solid transparent;
                transition: all 0.2s ease;
            }
            
            .message a:hover {
                border-bottom-color: var(--accent-blue);
                text-shadow: 0 0 8px rgba(88, 166, 255, 0.5);
            }
            
            /* ===== BLOCKQUOTES ===== */
            .message blockquote {
                border-left: 4px solid var(--accent-purple);
                background: rgba(163, 113, 247, 0.1);
                padding: 12px 16px;
                margin: 12px 0;
                border-radius: 0 8px 8px 0;
                font-style: italic;
                color: var(--text-secondary);
            }
            
            /* ===== TABLAS ===== */
            .message table {
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .message th {
                background: var(--primary-gradient);
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }
            
            .message td {
                padding: 10px 12px;
                border-bottom: 1px solid var(--border-color);
                background: var(--card-bg);
            }
            
            .message tr:hover td {
                background: rgba(88, 166, 255, 0.05);
            }
            
            /* ===== INDICADOR DE TYPING ===== */
            .typing-indicator {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 8px 12px;
                background: var(--card-bg);
                border-radius: 20px;
                margin: 8px 0;
            }
            
            .typing-dot {
                width: 8px;
                height: 8px;
                background: var(--accent-blue);
                border-radius: 50%;
                animation: typingBounce 1.4s infinite ease-in-out;
            }
            
            .typing-dot:nth-child(1) { animation-delay: 0s; }
            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typingBounce {
                0%, 80%, 100% {
                    transform: scale(0.6);
                    opacity: 0.5;
                }
                40% {
                    transform: scale(1);
                    opacity: 1;
                }
            }
            
            /* ===== BADGES DE ESTADO ===== */
            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }
            
            .status-badge.success {
                background: rgba(63, 185, 80, 0.15);
                color: var(--accent-green);
                border: 1px solid rgba(63, 185, 80, 0.3);
            }
            
            .status-badge.warning {
                background: rgba(210, 153, 34, 0.15);
                color: #d29922;
                border: 1px solid rgba(210, 153, 34, 0.3);
            }
            
            .status-badge.error {
                background: rgba(248, 81, 73, 0.15);
                color: #f85149;
                border: 1px solid rgba(248, 81, 73, 0.3);
            }
            
            .status-badge.info {
                background: rgba(88, 166, 255, 0.15);
                color: var(--accent-blue);
                border: 1px solid rgba(88, 166, 255, 0.3);
            }
            
            /* ===== SECCIONES DESTACADAS ===== */
            .highlight-section {
                background: linear-gradient(135deg, rgba(88, 166, 255, 0.05) 0%, rgba(163, 113, 247, 0.05) 100%);
                border: 1px solid rgba(88, 166, 255, 0.2);
                border-radius: 12px;
                padding: 16px;
                margin: 12px 0;
            }
            
            .highlight-section-title {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                color: var(--accent-blue);
                margin-bottom: 10px;
            }
            
            /* ===== BOTÓN COPIAR CÓDIGO ===== */
            .code-copy-btn {
                position: absolute;
                top: 8px;
                right: 8px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid var(--border-color);
                border-radius: 6px;
                padding: 6px 10px;
                color: var(--text-secondary);
                font-size: 12px;
                cursor: pointer;
                opacity: 0;
                transition: all 0.2s ease;
            }
            
            .message pre:hover .code-copy-btn {
                opacity: 1;
            }
            
            .code-copy-btn:hover {
                background: var(--accent-blue);
                color: white;
                border-color: var(--accent-blue);
            }
            
            .code-copy-btn.copied {
                background: var(--accent-green);
                border-color: var(--accent-green);
                color: white;
            }
            
            /* ===== SCROLL SUAVE ===== */
            #chatMessages {
                scroll-behavior: smooth;
            }
            
            /* ===== EFECTOS DE ENTRADA ===== */
            .fade-in {
                animation: fadeIn 0.5s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .slide-up {
                animation: slideUp 0.3s ease-out;
            }
            
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            /* ===== EMOJIS MEJORADOS ===== */
            .emoji-large {
                font-size: 1.5em;
                vertical-align: middle;
            }
            
            /* ===== SEPARADORES ===== */
            .message hr {
                border: none;
                height: 1px;
                background: linear-gradient(90deg, transparent, var(--border-color), transparent);
                margin: 16px 0;
            }
            
            /* ===== TOOLTIPS ===== */
            .tooltip {
                position: relative;
            }
            
            .tooltip::after {
                content: attr(data-tooltip);
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 12px;
                white-space: nowrap;
                opacity: 0;
                visibility: hidden;
                transition: all 0.2s ease;
                z-index: 1000;
            }
            
            .tooltip:hover::after {
                opacity: 1;
                visibility: visible;
                transform: translateX(-50%) translateY(-5px);
            }
            
            /* ===== MEJORAS EN INPUTS ===== */
            #messageInput {
                background: var(--card-bg) !important;
                border: 2px solid var(--border-color) !important;
                border-radius: 12px !important;
                color: var(--text-primary) !important;
                padding: 14px 16px !important;
                font-size: 15px !important;
                transition: all 0.2s ease !important;
            }
            
            #messageInput:focus {
                border-color: var(--accent-blue) !important;
                box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15) !important;
                outline: none !important;
            }
            
            #messageInput::placeholder {
                color: var(--text-secondary) !important;
            }
            
            /* ===== BOTÓN ENVIAR ===== */
            .send-btn, button[type="submit"] {
                background: var(--primary-gradient) !important;
                border: none !important;
                border-radius: 10px !important;
                color: white !important;
                font-weight: 600 !important;
                padding: 12px 20px !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
            }
            
            .send-btn:hover, button[type="submit"]:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
            }
            
            /* ===== PROGRESS BAR ===== */
            .progress-bar {
                width: 100%;
                height: 4px;
                background: var(--border-color);
                border-radius: 2px;
                overflow: hidden;
            }
            
            .progress-bar-fill {
                height: 100%;
                background: var(--primary-gradient);
                border-radius: 2px;
                transition: width 0.3s ease;
            }
            
            /* ===== CARDS ===== */
            .info-card {
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 16px;
                margin: 12px 0;
                transition: all 0.2s ease;
            }
            
            .info-card:hover {
                border-color: var(--accent-blue);
                transform: translateY(-2px);
                box-shadow: var(--shadow-glow);
            }
            
            /* ===== STREAMING MESSAGE ===== */
            .message.streaming {
                border-color: var(--accent-blue);
                animation: streamingPulse 2s infinite;
            }
            
            @keyframes streamingPulse {
                0%, 100% { box-shadow: 0 0 15px rgba(88, 166, 255, 0.2); }
                50% { box-shadow: 0 0 25px rgba(88, 166, 255, 0.4); }
            }
            
            /* ===== CHECKBOX ESTILIZADO ===== */
            .styled-checkbox {
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
            }
            
            .styled-checkbox input {
                display: none;
            }
            
            .styled-checkbox .checkmark {
                width: 20px;
                height: 20px;
                border: 2px solid var(--border-color);
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }
            
            .styled-checkbox input:checked + .checkmark {
                background: var(--accent-green);
                border-color: var(--accent-green);
            }
            
            .styled-checkbox input:checked + .checkmark::after {
                content: '✓';
                color: white;
                font-size: 12px;
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Agregar botón de copiar a bloques de código
    function addCopyButtons() {
        const codeBlocks = document.querySelectorAll('.message pre:not(.copy-btn-added)');
        
        codeBlocks.forEach(pre => {
            pre.classList.add('copy-btn-added');
            pre.style.position = 'relative';
            
            const btn = document.createElement('button');
            btn.className = 'code-copy-btn';
            btn.textContent = '📋 Copiar';
            btn.onclick = async (e) => {
                e.stopPropagation();
                const code = pre.querySelector('code') || pre;
                try {
                    await navigator.clipboard.writeText(code.textContent);
                    btn.textContent = '✓ Copiado';
                    btn.classList.add('copied');
                    setTimeout(() => {
                        btn.textContent = '📋 Copiar';
                        btn.classList.remove('copied');
                    }, 2000);
                } catch (e) {
                    console.error('Error copiando:', e);
                }
            };
            
            pre.appendChild(btn);
        });
    }
    
    // Crear indicador de typing
    function createTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        indicator.style.display = 'none';
        return indicator;
    }
    
    // Mostrar/ocultar indicador de typing
    function showTyping(show = true) {
        let indicator = document.getElementById('typingIndicator');
        if (!indicator) {
            indicator = createTypingIndicator();
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.appendChild(indicator);
            }
        }
        indicator.style.display = show ? 'inline-flex' : 'none';
        
        if (show) {
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
    }
    
    // Crear badge de estado
    function createStatusBadge(type, text) {
        const badge = document.createElement('span');
        badge.className = `status-badge ${type}`;
        badge.innerHTML = `${getStatusIcon(type)} ${text}`;
        return badge;
    }
    
    function getStatusIcon(type) {
        const icons = {
            success: '✓',
            warning: '⚠',
            error: '✕',
            info: 'ℹ'
        };
        return icons[type] || 'ℹ';
    }
    
    // Mejorar mensaje existente
    function enhanceMessage(element) {
        if (!element || element.dataset.enhanced) return;
        element.dataset.enhanced = 'true';
        
        // Agregar botones de copiar a bloques de código
        const codeBlocks = element.querySelectorAll('pre:not(.copy-btn-added)');
        codeBlocks.forEach(pre => {
            pre.classList.add('copy-btn-added');
            pre.style.position = 'relative';
            
            const btn = document.createElement('button');
            btn.className = 'code-copy-btn';
            btn.textContent = '📋 Copiar';
            btn.onclick = async (e) => {
                e.stopPropagation();
                const code = pre.querySelector('code') || pre;
                try {
                    await navigator.clipboard.writeText(code.textContent);
                    btn.textContent = '✓ Copiado';
                    btn.classList.add('copied');
                    setTimeout(() => {
                        btn.textContent = '📋 Copiar';
                        btn.classList.remove('copied');
                    }, 2000);
                } catch (e) {
                    console.error('Error copiando:', e);
                }
            };
            pre.appendChild(btn);
        });
        
        // Destacar secciones importantes
        const text = element.textContent || '';
        if (text.includes('✅') || text.includes('COMPLETADO') || text.includes('ÉXITO')) {
            element.style.borderLeftColor = 'var(--accent-green)';
        } else if (text.includes('❌') || text.includes('ERROR') || text.includes('FALLO')) {
            element.style.borderLeftColor = '#f85149';
        } else if (text.includes('⚠') || text.includes('ADVERTENCIA')) {
            element.style.borderLeftColor = '#d29922';
        }
    }
    
    // Aplicar estilos a mensajes existentes
    function enhanceExistingMessages() {
        const messages = document.querySelectorAll('.message:not([data-enhanced])');
        messages.forEach(enhanceMessage);
    }
    
    // Inicializar
    function init() {
        injectStyles();
        enhanceExistingMessages();
        
        console.log('[UIPolish] Estilos profesionales aplicados');
        
        // Observer para nuevos mensajes
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1 && node.classList && node.classList.contains('message')) {
                            setTimeout(() => enhanceMessage(node), 100);
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
        setTimeout(init, 500);
    }
    
    // Exponer API global
    window.UIPolish = {
        init: init,
        enhance: enhanceMessage,
        enhanceAll: enhanceExistingMessages,
        showTyping: showTyping,
        createBadge: createStatusBadge,
        addCopyButtons: addCopyButtons
    };
    
})();
