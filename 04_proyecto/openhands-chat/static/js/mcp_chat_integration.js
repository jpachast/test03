/**
 * MCP Chat Integration - Integración del Model Context Protocol en el Chat
 * Gestiona contexto entre mensajes automáticamente
 */

class MCPChatIntegration {
    constructor() {
        this.conversationId = null;
        this.sessionId = null;
        this.contextCache = {};
        this.initialized = false;
    }

    async init(conversationId) {
        this.conversationId = conversationId;
        try {
            const response = await fetch(`/api/mcp/session/${conversationId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                this.initialized = true;
                console.log('[MCP] Sesión iniciada:', this.sessionId);
            }
        } catch (e) {
            console.warn('[MCP] No se pudo iniciar sesión:', e);
        }
    }

    async addContext(type, content, metadata = {}) {
        if (!this.initialized) return;
        try {
            await fetch(`/api/mcp/context/${this.conversationId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, content, metadata })
            });
        } catch (e) {
            console.warn('[MCP] Error agregando contexto:', e);
        }
    }

    async getRelevantContext(query) {
        if (!this.initialized) return null;
        try {
            const response = await fetch(`/api/mcp/context/${this.conversationId}/relevant?query=${encodeURIComponent(query)}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {
            console.warn('[MCP] Error obteniendo contexto:', e);
        }
        return null;
    }

    async processUserMessage(message) {
        await this.addContext('conversation', message, { role: 'user' });
        const context = await this.getRelevantContext(message);
        return context;
    }

    async processAgentResponse(response) {
        await this.addContext('conversation', response, { role: 'assistant' });
        this.extractAndSaveKeyInfo(response);
    }

    extractAndSaveKeyInfo(response) {
        const patterns = [
            { regex: /(?:archivo|file)\s+([\w./]+)/gi, type: 'file' },
            { regex: /(?:función|function|def)\s+(\w+)/gi, type: 'function' },
            { regex: /(?:error|bug|issue):\s*(.+)/gi, type: 'issue' },
            { regex: /(?:solución|fix|solution):\s*(.+)/gi, type: 'solution' }
        ];

        patterns.forEach(({ regex, type }) => {
            const matches = response.matchAll(regex);
            for (const match of matches) {
                this.addContext('memory', match[1], { extracted_type: type });
            }
        });
    }

    showContextIndicator(element, contextData) {
        if (!contextData || !contextData.contexts || contextData.contexts.length === 0) return;

        const indicator = document.createElement('div');
        indicator.className = 'mcp-context-indicator';
        indicator.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 12px;
                border-radius: 8px;
                margin-bottom: 10px;
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <span style="font-size: 16px;">🔗</span>
                <span><strong>Contexto MCP:</strong> ${contextData.contexts.length} items relevantes</span>
                <span style="opacity: 0.7; margin-left: auto;">${contextData.current_tokens || 0} tokens</span>
            </div>
        `;
        
        element.insertBefore(indicator, element.firstChild);
    }
}

// Instancia global
window.mcpChat = new MCPChatIntegration();

// Auto-inicializar cuando se carga una conversación
document.addEventListener('DOMContentLoaded', () => {
    const pathParts = window.location.pathname.split('/');
    const conversationId = pathParts[pathParts.indexOf('chat') + 1];
    if (conversationId && !isNaN(conversationId)) {
        window.mcpChat.init(parseInt(conversationId));
    }
});

// Integrar con el sistema de mensajes existente
if (typeof window.originalSendMessage === 'undefined' && typeof window.sendMessage === 'function') {
    window.originalSendMessage = window.sendMessage;
    window.sendMessage = async function(...args) {
        const message = args[0] || document.querySelector('#message-input')?.value;
        if (message && window.mcpChat.initialized) {
            await window.mcpChat.processUserMessage(message);
        }
        return window.originalSendMessage.apply(this, args);
    };
}

console.log('[MCP] Chat Integration loaded');
