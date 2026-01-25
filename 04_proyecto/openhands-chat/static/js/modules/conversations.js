/**
 * Conversations Module - Conversation management
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    async function loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            const data = await response.json();
            
            const container = document.getElementById('conversationsList');
            if (!container) return;
            
            const conversations = data.conversations || [];
            
            if (conversations.length === 0) {
                container.innerHTML = '<div class="no-conversations">No hay conversaciones aún. ¡Empieza una nueva!</div>';
                return;
            }
            
            container.innerHTML = '';
            conversations.slice(0, 10).forEach(conv => {
                const timeAgo = getTimeAgo(conv.updated_at || conv.created_at);
                const repoInfo = conv.repo_owner && conv.repo_name 
                    ? `${conv.repo_owner}/${conv.repo_name}` 
                    : conv.project_name || 'Sin proyecto';
                
                const projName = (conv.project_name || '').replace(/'/g, "\\'");
                const owner = (conv.repo_owner || '').replace(/'/g, "\\'");
                const repo = (conv.repo_name || '').replace(/'/g, "\\'");
                const branch = (conv.branch || '').replace(/'/g, "\\'");
                
                container.innerHTML += `
                    <div class="conversation-item" onclick="openConversation(${conv.id}, '${projName}', '${owner}', '${repo}', '${branch}')">
                        <div class="conv-status ${conv.status === 'done' ? 'done' : ''}"></div>
                        <div class="conv-info">
                            <div class="conv-title">${conv.title || 'Sin título'}</div>
                            <div class="conv-repo">
                                <span>📦</span>
                                <span>${repoInfo}</span>
                                ${conv.branch ? `<span>🔀 ${conv.branch}</span>` : ''}
                            </div>
                        </div>
                        <div class="conv-time">${timeAgo}</div>
                        <div class="conv-menu">⋮</div>
                    </div>
                `;
            });
            
            const viewMore = document.getElementById('viewMore');
            if (viewMore && conversations.length > 10) {
                viewMore.style.display = 'block';
            }
        } catch (error) {
            console.error('Error cargando conversaciones:', error);
            const container = document.getElementById('conversationsList');
            if (container) {
                container.innerHTML = '<div class="no-conversations">Error cargando conversaciones</div>';
            }
        }
    }
    
    function getTimeAgo(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'ahora';
        if (diff < 3600) return `${Math.floor(diff/60)}m atrás`;
        if (diff < 86400) return `${Math.floor(diff/3600)}h atrás`;
        return `${Math.floor(diff/86400)}d atrás`;
    }
    
    async function openConversation(convId, projectName, repoOwner, repoName, branch, preloadedMessages = null) {
        window.currentProject = projectName;
        window.currentConversationId = convId;
        
        const convIdInput = document.getElementById('currentConversationId');
        if (convIdInput) convIdInput.value = convId;
        
        window.history.pushState({convId: convId}, '', `/chat/${convId}`);
        
        const repoFullName = repoOwner && repoName ? `${repoOwner}/${repoName}` : projectName;
        if (window.showChat) window.showChat(projectName, repoFullName, branch);
        
        if (window.showCodeTabs) window.showCodeTabs(repoName || projectName);
        window.codeServerLoaded = false;
        window.browserLoaded = false;
        
        if (window.clearTerminal) window.clearTerminal();
        
        const appPlaceholder = document.getElementById('appPlaceholder');
        const appFrame = document.getElementById('appFrame');
        if (appPlaceholder) appPlaceholder.style.display = 'flex';
        if (appFrame) appFrame.style.display = 'none';
        
        // PRE-INICIAR servidores
        fetch('/api/code-server/prestart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ conversation_id: convId })
        }).catch(() => {});
        
        fetch('/api/app-server/prestart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ conversation_id: convId })
        }).catch(() => {});
        
        if (repoOwner && repoName) {
            if (window.updateGitBar) window.updateGitBar(repoOwner, repoName, branch);
            if (window.refreshBranchInfo) window.refreshBranchInfo(convId);
        }
        
        // Cargar mensajes
        try {
            let messages = preloadedMessages;
            
            if (!messages) {
                const response = await fetch(`/api/conversations/${convId}`);
                const data = await response.json();
                messages = data.messages;
            }
            
            const msgContainer = document.getElementById('chatMessages');
            if (!msgContainer) return;
            
            msgContainer.innerHTML = '';
            if (messages && messages.length > 0) {
                messages.forEach(msg => {
                    const div = document.createElement('div');
                    div.className = `message ${msg.role}`;
                    if (msg.role === 'assistant') {
                        div.innerHTML = '🤖 ' + (window.formatMessage ? window.formatMessage(msg.content) : msg.content);
                    } else {
                        div.innerHTML = msg.content;
                    }
                    msgContainer.appendChild(div);
                });
                msgContainer.scrollTop = msgContainer.scrollHeight;
            } else {
                msgContainer.innerHTML = '<div class="message system">👋 ¡Hola! ¿En qué puedo ayudarte?</div>';
            }
        } catch (error) {
            console.error('Error cargando mensajes:', error);
        }
    }
    
    function startNewConversation() {
        window.currentProject = '';
        window.currentConversationId = null;
        if (window.showChat) window.showChat('', '', '');
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '<div class="message system">👋 ¡Hola! Soy tu asistente de desarrollo. ¿Qué quieres crear hoy?</div>';
        }
    }
    
    // Exponer globalmente
    window.ConversationsModule = {
        load: loadConversations,
        open: openConversation,
        startNew: startNewConversation,
        getTimeAgo: getTimeAgo
    };
    
    window.loadConversations = loadConversations;
    window.openConversation = openConversation;
    window.startNewConversation = startNewConversation;
    window.getTimeAgo = getTimeAgo;
    
})();
