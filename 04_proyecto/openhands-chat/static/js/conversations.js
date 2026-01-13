        let conversations = [];
        let selectedConvId = null;
        let openMenuId = null;
        
        // Cargar conversaciones
        async function loadConversations() {
            try {
                const response = await fetch('/api/conversations');
                const data = await response.json();
                conversations = data.conversations || [];
                renderConversations();
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        function renderConversations() {
            const list = document.getElementById('conversationsList');
            
            if (conversations.length === 0) {
                list.innerHTML = `
                    <div class="empty-state">
                        <h3>No hay conversaciones</h3>
                        <p>Inicia una nueva conversación desde el inicio</p>
                    </div>
                `;
                return;
            }
            
            list.innerHTML = conversations.map(conv => {
                const timeAgo = getTimeAgo(conv.created_at);
                return `
                    <div class="conversation-item" onclick="openConversation(${conv.id})">
                        <div class="conv-status ${conv.status}"></div>
                        <div class="conv-info">
                            <div class="conv-title">
                                <span class="conv-title-text">${conv.title}</span>
                            </div>
                            <div class="conv-meta">
                                <span class="conv-repo">📦 ${conv.repo_owner}/${conv.repo_name}</span>
                                <span>🔀 ${conv.branch}</span>
                            </div>
                        </div>
                        <span class="conv-time">${timeAgo}</span>
                        <div class="conv-menu">
                            <button class="menu-btn" onclick="toggleMenu(event, ${conv.id})">⋮</button>
                            <div id="menu-${conv.id}" class="menu-dropdown">
                                <div class="menu-item" onclick="openRenameModal(event, ${conv.id}, '${conv.title.replace(/'/g, "\\'")}')">
                                    ✏️ Renombrar
                                </div>
                                <div class="menu-item danger" onclick="openDeleteModal(event, ${conv.id}, '${conv.title.replace(/'/g, "\\'")}')">
                                    🗑️ Eliminar conversación
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function getTimeAgo(dateStr) {
            const date = new Date(dateStr);
            const now = new Date();
            const diff = now - date;
            
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(diff / 3600000);
            const days = Math.floor(diff / 86400000);
            
            if (minutes < 1) return 'ahora';
            if (minutes < 60) return `${minutes}m atrás`;
            if (hours < 24) return `${hours}h atrás`;
            return `${days}d atrás`;
        }
        
        function toggleMenu(event, convId) {
            event.stopPropagation();
            
            // Cerrar otros menus
            document.querySelectorAll('.menu-dropdown').forEach(m => m.classList.remove('show'));
            
            const menu = document.getElementById(`menu-${convId}`);
            if (openMenuId === convId) {
                openMenuId = null;
            } else {
                menu.classList.add('show');
                openMenuId = convId;
            }
        }
        
        // Cerrar menus al hacer clic fuera
        document.addEventListener('click', () => {
            document.querySelectorAll('.menu-dropdown').forEach(m => m.classList.remove('show'));
            openMenuId = null;
        });
        
        function openConversation(convId) {
            window.location.href = `/chat/${convId}`;
        }
        
        // Renombrar
        function openRenameModal(event, convId, currentTitle) {
            event.stopPropagation();
            selectedConvId = convId;
            document.getElementById('renameInput').value = currentTitle;
            document.getElementById('renameModal').classList.add('show');
        }
        
        function closeRenameModal() {
            document.getElementById('renameModal').classList.remove('show');
            selectedConvId = null;
        }
        
        async function saveRename() {
            const newTitle = document.getElementById('renameInput').value.trim();
            if (!newTitle || !selectedConvId) return;
            
            try {
                await fetch(`/api/conversations/${selectedConvId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: newTitle })
                });
                closeRenameModal();
                loadConversations();
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        // Eliminar
        function openDeleteModal(event, convId, title) {
            event.stopPropagation();
            selectedConvId = convId;
            document.getElementById('deleteConvName').textContent = title;
            document.getElementById('deleteModal').classList.add('show');
        }
        
        function closeDeleteModal() {
            document.getElementById('deleteModal').classList.remove('show');
            selectedConvId = null;
        }
        
        async function confirmDelete() {
            if (!selectedConvId) return;
            
            try {
                await fetch(`/api/conversations/${selectedConvId}`, {
                    method: 'DELETE'
                });
                closeDeleteModal();
                loadConversations();
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        // Iniciar
        loadConversations();
