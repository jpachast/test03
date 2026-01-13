        // === ESTADO GLOBAL ===
        let currentProject = '';
        let selectedRepo = null;
        let repos = [];
        let currentView = 'chat';
        let codeServerLoaded = false;
        let isMainProject = false;
        
        let chatMessages = null;
        let messageInput = null;
        let repoSelect = null;
        let branchSelect = null;
        let launchBtn = null;
        
        // === INICIALIZACIÓN ===
        // Verificar si estamos en /chat/{id} o si hay ?conv= en URL
        const pathMatch = window.location.pathname.match(/^\/chat\/(\d+)$/);
        const urlParams = new URLSearchParams(window.location.search);
        const convIdFromUrl = pathMatch ? pathMatch[1] : urlParams.get('conv');
        
        // Si hay conv en URL, ocultar home inmediatamente
        if (convIdFromUrl) {
            document.getElementById('homeFullscreen').style.display = 'none';
            document.getElementById('chatPage').style.display = 'flex';
        }
        
        document.addEventListener('DOMContentLoaded', async () => {
            // Inicializar elementos del DOM
            chatMessages = document.getElementById('chatMessages');
            messageInput = document.getElementById('messageInput');
            repoSelect = document.getElementById('repoSelect');
            branchSelect = document.getElementById('branchSelect');
            launchBtn = document.getElementById('launchBtn');
            
            console.log('DOM cargado, chatMessages:', chatMessages);
            
            // Si hay conv en URL, abrir directamente sin cargar home
            if (convIdFromUrl) {
                await openConversationById(parseInt(convIdFromUrl));
            } else {
                await loadGitHubRepos();
                await loadConversations();
            }
        });
        
        // Abrir conversación por ID (desde URL)
        async function openConversationById(convId) {
            try {
                console.log('Abriendo conversación:', convId);
                const response = await fetch(`/api/conversations/${convId}`);
                if (!response.ok) {
                    console.error('Conversación no encontrada');
                    return;
                }
                const data = await response.json();
                console.log('Datos cargados:', data);
                const conv = data.conversation;
                
                if (conv) {
                    // Pasar también los mensajes ya cargados
                    await openConversation(
                        conv.id,
                        conv.project_name || '',
                        conv.repo_owner || '',
                        conv.repo_name || '',
                        conv.branch || 'main',
                        data.messages  // Mensajes ya cargados
                    );
                }
            } catch (error) {
                console.error('Error abriendo conversación:', error);
            }
        }
        
        // === GITHUB ===
        async function loadGitHubRepos() {
            try {
                const response = await fetch('/api/github/repos');
                if (response.status === 401) {
                    repoSelect.innerHTML = '<option value="">GitHub no configurado</option>';
                    repoSelect.innerHTML += '<option value="_config">⚙️ Configurar GitHub...</option>';
                    return;
                }
                
                const data = await response.json();
                repos = data.repos || [];
                
                repoSelect.innerHTML = '<option value="">Selecciona un repositorio...</option>';
                repos.forEach(repo => {
                    const opt = document.createElement('option');
                    opt.value = `${repo.owner}/${repo.name}`;
                    opt.textContent = `${repo.private ? '🔒' : '📂'} ${repo.full_name}`;
                    opt.dataset.owner = repo.owner;
                    opt.dataset.name = repo.name;
                    opt.dataset.defaultBranch = repo.default_branch;
                    repoSelect.appendChild(opt);
                });
            } catch (error) {
                console.error('Error cargando repos:', error);
                repoSelect.innerHTML = '<option value="">Error cargando repos</option>';
            }
        }
        
        async function onRepoSelect() {
            const value = repoSelect.value;
            
            if (value === '_config') {
                window.location.href = '/settings?tab=integraciones';
                return;
            }
            
            if (!value) {
                branchSelect.disabled = true;
                branchSelect.innerHTML = '<option value="">Selecciona branch...</option>';
                launchBtn.disabled = true;
                return;
            }
            
            const option = repoSelect.options[repoSelect.selectedIndex];
            selectedRepo = {
                owner: option.dataset.owner,
                name: option.dataset.name,
                defaultBranch: option.dataset.defaultBranch
            };
            
            // Cargar branches
            branchSelect.innerHTML = '<option value="">Cargando branches...</option>';
            branchSelect.disabled = true;
            
            try {
                const response = await fetch(`/api/github/repos/${selectedRepo.owner}/${selectedRepo.name}/branches`);
                const data = await response.json();
                
                branchSelect.innerHTML = '';
                (data.branches || []).forEach(branch => {
                    const opt = document.createElement('option');
                    opt.value = branch.name;
                    opt.textContent = `🔀 ${branch.name}${branch.protected ? ' 🔒' : ''}`;
                    if (branch.name === selectedRepo.defaultBranch) {
                        opt.selected = true;
                    }
                    branchSelect.appendChild(opt);
                });
                
                branchSelect.disabled = false;
                launchBtn.disabled = false;
            } catch (error) {
                console.error('Error cargando branches:', error);
                branchSelect.innerHTML = '<option value="">Error cargando branches</option>';
            }
        }
        
        async function launchRepo() {
            if (!selectedRepo || !branchSelect.value) return;
            
            launchBtn.disabled = true;
            launchBtn.textContent = 'Clonando...';
            
            try {
                const response = await fetch('/api/github/launch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        owner: selectedRepo.owner,
                        repo: selectedRepo.name,
                        branch: branchSelect.value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentProject = data.project_name;
                    currentConversationId = data.conversation_id;
                    document.getElementById('currentConversationId').value = data.conversation_id;
                    showChat(data.project_name, `${selectedRepo.owner}/${selectedRepo.name}`, branchSelect.value);
                    chatMessages.innerHTML = '<div class="message system">👋 ¡Hola! Repositorio clonado correctamente. ¿Qué quieres hacer?</div>';
                } else {
                    alert('Error: ' + (data.error || 'No se pudo clonar'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                launchBtn.disabled = false;
                launchBtn.textContent = 'Launch';
            }
        }
        
        // === CONVERSACIONES ===
        async function loadConversations() {
            try {
                const response = await fetch('/api/conversations');
                const data = await response.json();
                
                const container = document.getElementById('conversationsList');
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
                    
                    // Escapar valores para el onclick
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
                
                if (conversations.length > 10) {
                    document.getElementById('viewMore').style.display = 'block';
                }
            } catch (error) {
                console.error('Error cargando conversaciones:', error);
                document.getElementById('conversationsList').innerHTML = 
                    '<div class="no-conversations">Error cargando conversaciones</div>';
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
            currentProject = projectName;
            currentConversationId = convId;
            document.getElementById('currentConversationId').value = convId;
            
            // Actualizar URL a /chat/{id}
            window.history.pushState({convId: convId}, '', `/chat/${convId}`);
            
            const repoFullName = repoOwner && repoName ? `${repoOwner}/${repoName}` : projectName;
            showChat(projectName, repoFullName, branch);
            
            // Mostrar/ocultar tabs de código según el proyecto
            showCodeTabs(repoName || projectName);
            codeServerLoaded = false; // Reset para nuevo proyecto
            
            // Actualizar barra de Git
            if (repoOwner && repoName) {
                updateGitBar(repoOwner, repoName, branch);
            }
            
            // Cargar mensajes de la conversación
            try {
                let messages = preloadedMessages;
                
                // Si no tenemos mensajes precargados, cargarlos
                if (!messages) {
                    const response = await fetch(`/api/conversations/${convId}`);
                    const data = await response.json();
                    messages = data.messages;
                }
                
                console.log('Mensajes a mostrar:', messages);
                
                // Asegurar que chatMessages existe
                const msgContainer = document.getElementById('chatMessages');
                if (!msgContainer) {
                    console.error('No se encontró chatMessages');
                    return;
                }
                
                msgContainer.innerHTML = '';
                if (messages && messages.length > 0) {
                    messages.forEach(msg => {
                        console.log('Agregando mensaje:', msg.role, msg.content);
                        const div = document.createElement('div');
                        div.className = `message ${msg.role}`;
                        if (msg.role === 'assistant') {
                            div.innerHTML = '🤖 ' + formatMessage(msg.content);
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
            currentProject = '';
            currentConversationId = null;
            showChat('', '', '');
            chatMessages.innerHTML = '<div class="message system">👋 ¡Hola! Soy tu asistente de desarrollo. ¿Qué quieres crear hoy?</div>';
        }
        
        // === NAVEGACIÓN ===
        let currentConversationId = null;
        
        function showChat(projectName, repoFullName, branch) {
            document.getElementById('homeFullscreen').style.display = 'none';
            document.getElementById('chatPage').style.display = 'flex';
            document.getElementById('currentProject').value = projectName;
            document.getElementById('repoName').textContent = repoFullName || projectName || 'Nueva conversación';
            document.getElementById('repoBranch').textContent = branch ? `🔀 ${branch}` : '';
            currentProject = projectName;
            
            // Actualizar barra de git - ocultar badge si no hay branch real
            document.getElementById('gitRepoName').textContent = repoFullName || projectName || '';
            const branchBadge = document.getElementById('gitBranchBadge');
            if (branch && branch !== '') {
                document.getElementById('gitBranchName').textContent = branch;
                branchBadge.style.display = 'flex';
            } else {
                branchBadge.style.display = 'none';
            }
            
            if (messageInput) messageInput.focus();
        }
        
        function goHome() {
            document.getElementById('homeFullscreen').style.display = 'flex';
            document.getElementById('chatPage').style.display = 'none';
            currentConversationId = null;
            loadConversations();
            // Limpiar URL
            window.history.pushState({}, '', '/');
            // Reset view y code-server
            switchView('chat');
            stopCodeServer();
        }
        
        // === TABS CHAT/CÓDIGO ===
        function switchView(view) {
            currentView = view;
            const appView = document.getElementById('appView');
            const codeViewRight = document.getElementById('codeViewRight');
            const tabChat = document.getElementById('tabChat');
            const tabCode = document.getElementById('tabCode');
            const tabApp = document.getElementById('tabApp');
            
            // Resetear todos los tabs
            tabChat.classList.remove('active');
            tabCode.classList.remove('active');
            tabApp.classList.remove('active');
            
            if (view === 'chat' || view === 'app') {
                // Mostrar vista de aplicación en panel derecho
                appView.style.display = 'block';
                codeViewRight.style.display = 'none';
                if (view === 'chat') {
                    tabChat.classList.add('active');
                } else {
                    tabApp.classList.add('active');
                }
            } else if (view === 'code') {
                // Mostrar código en panel derecho
                appView.style.display = 'none';
                codeViewRight.style.display = 'block';
                tabCode.classList.add('active');
                // Iniciar code-server si no está cargado
                if (!codeServerLoaded) {
                    startCodeServer();
                }
            }
        }
        
        async function startCodeServer() {
            const loading = document.getElementById('codeLoadingRight');
            const frame = document.getElementById('codeServerFrameRight');
            
            loading.style.display = 'block';
            frame.style.display = 'none';
            
            try {
                const response = await fetch('/api/code-server/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ conversation_id: currentConversationId })
                });
                
                const data = await response.json();
                
                if (response.status === 403) {
                    // Es el proyecto principal
                    loading.innerHTML = '<p>⚠️ El editor de código no está disponible para el proyecto principal (test03)</p>';
                    return;
                }
                
                if (data.status === 'started' || data.status === 'running') {
                    // Esperar un poco más para que code-server inicie completamente
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    frame.src = '/code-server/?folder=' + encodeURIComponent(data.path);
                    frame.style.display = 'block';
                    loading.style.display = 'none';
                    codeServerLoaded = true;
                } else {
                    loading.innerHTML = `<p>❌ Error: ${data.message || 'No se pudo iniciar el editor'}</p>`;
                }
            } catch (error) {
                loading.innerHTML = `<p>❌ Error: ${error.message}</p>`;
            }
        }
        
        async function stopCodeServer() {
            try {
                await fetch('/api/code-server/stop', { method: 'POST' });
                codeServerLoaded = false;
                const frame = document.getElementById('codeServerFrameRight');
                if (frame) frame.src = 'about:blank';
            } catch (error) {
                console.error('Error deteniendo code-server:', error);
            }
        }
        
        function showCodeTabs(repoName) {
            // Mostrar tabs solo si NO es el proyecto principal (test03)
            const viewTabs = document.getElementById('viewTabs');
            isMainProject = repoName && repoName.toLowerCase().includes('test03');
            
            if (isMainProject) {
                viewTabs.style.display = 'none';
            } else {
                viewTabs.style.display = 'flex';
            }
        }
        
        function showHelp() {
            alert('🤖 OpenHands Chat\n\n1. Configura tu API key en Configuración\n2. Conecta tu cuenta de GitHub\n3. Selecciona un repositorio o empieza desde cero\n4. ¡Empieza a construir!');
        }
        
        // === ACCIONES GIT ===
        let currentGitInfo = { owner: '', repo: '', branch: 'main' };
        
        function updateGitBar(owner, repo, branch) {
            currentGitInfo = { owner, repo, branch: branch || 'main' };
            document.getElementById('gitRepoName').textContent = `${owner}/${repo}`;
            document.getElementById('gitBranchName').textContent = branch || 'main';
        }
        
        // SVG icons para los botones Git
        const gitIcons = {
            pull: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M7.47 10.78a.75.75 0 001.06 0l3.75-3.75a.75.75 0 00-1.06-1.06L8.75 8.44V1.75a.75.75 0 00-1.5 0v6.69L4.78 5.97a.75.75 0 00-1.06 1.06l3.75 3.75zM3.75 13a.75.75 0 000 1.5h8.5a.75.75 0 000-1.5h-8.5z"/></svg>',
            push: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M8.53 1.22a.75.75 0 00-1.06 0L3.72 4.97a.75.75 0 001.06 1.06l2.47-2.47v6.69a.75.75 0 001.5 0V3.56l2.47 2.47a.75.75 0 101.06-1.06L8.53 1.22zM3.75 13a.75.75 0 000 1.5h8.5a.75.75 0 000-1.5h-8.5z"/></svg>',
            pr: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/></svg>',
            loading: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" class="spin"><path d="M8 0a8 8 0 100 16A8 8 0 008 0zm0 1.5a6.5 6.5 0 110 13 6.5 6.5 0 010-13z" opacity="0.3"/><path d="M8 0a8 8 0 018 8h-1.5A6.5 6.5 0 008 1.5V0z"/></svg>'
        };
        
        async function gitPull() {
            if (!currentGitInfo.owner || !currentGitInfo.repo) {
                alert('No hay repositorio seleccionado');
                return;
            }
            
            const btn = event.target.closest('.git-btn');
            btn.disabled = true;
            btn.innerHTML = gitIcons.loading + ' Pulling...';
            
            try {
                const response = await fetch('/api/git/pull', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project: currentProject,
                        owner: currentGitInfo.owner,
                        repo: currentGitInfo.repo,
                        branch: currentGitInfo.branch
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(`✅ Pull exitoso: ${data.message || 'Cambios actualizados'}`, 'system');
                } else {
                    addMessage(`❌ Error en Pull: ${data.error || 'Error desconocido'}`, 'system');
                }
            } catch (error) {
                addMessage(`❌ Error: ${error.message}`, 'system');
            } finally {
                btn.disabled = false;
                btn.innerHTML = gitIcons.pull + ' Pull';
            }
        }
        
        async function gitPush() {
            if (!currentGitInfo.owner || !currentGitInfo.repo) {
                alert('No hay repositorio seleccionado');
                return;
            }
            
            const commitMsg = prompt('Mensaje del commit:', 'Actualización desde OpenHands Chat');
            if (!commitMsg) return;
            
            const btn = event.target.closest('.git-btn');
            btn.disabled = true;
            btn.innerHTML = gitIcons.loading + ' Pushing...';
            
            try {
                const response = await fetch('/api/git/push', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project: currentProject,
                        owner: currentGitInfo.owner,
                        repo: currentGitInfo.repo,
                        branch: currentGitInfo.branch,
                        commit_message: commitMsg
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(`✅ Push exitoso: ${data.message || 'Cambios enviados al repositorio'}`, 'system');
                } else {
                    addMessage(`❌ Error en Push: ${data.error || 'Error desconocido'}`, 'system');
                }
            } catch (error) {
                addMessage(`❌ Error: ${error.message}`, 'system');
            } finally {
                btn.disabled = false;
                btn.innerHTML = gitIcons.push + ' Push';
            }
        }
        
        async function createPR() {
            if (!currentGitInfo.owner || !currentGitInfo.repo) {
                alert('No hay repositorio seleccionado');
                return;
            }
            
            const title = prompt('Título del Pull Request:', 'Cambios desde OpenHands Chat');
            if (!title) return;
            
            const body = prompt('Descripción (opcional):', '');
            
            const btn = event.target.closest('.git-btn');
            btn.disabled = true;
            btn.innerHTML = gitIcons.loading + ' Creando...';
            
            try {
                const response = await fetch('/api/git/create-pr', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project: currentProject,
                        owner: currentGitInfo.owner,
                        repo: currentGitInfo.repo,
                        branch: currentGitInfo.branch,
                        title: title,
                        body: body || ''
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(`✅ PR creado: <a href="${data.url}" target="_blank">${data.url}</a>`, 'system');
                } else {
                    addMessage(`❌ Error creando PR: ${data.error || 'Error desconocido'}`, 'system');
                }
            } catch (error) {
                addMessage(`❌ Error: ${error.message}`, 'system');
            } finally {
                btn.disabled = false;
                btn.innerHTML = gitIcons.pr + ' Solicitud de PR';
            }
        }
        
        // === MENSAJES ===
        async function loadMessages(conversationId) {
            if (!conversationId) return;
            
            try {
                const response = await fetch(`/api/conversations/${conversationId}`);
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    chatMessages.innerHTML = '';
                    data.messages.forEach(msg => {
                        addMessage(msg.content, msg.role);
                    });
                } else {
                    chatMessages.innerHTML = '<div class="message system">👋 ¡Hola! Soy tu asistente de desarrollo. ¿En qué puedo ayudarte?</div>';
                }
            } catch (error) {
                console.error('Error cargando mensajes:', error);
            }
        }
        
        function formatMessage(text) {
            if (!text) return '';
            text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
            text = text.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank">$1</a>');
            text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>');
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            text = text.replace(/\n\n/g, '</p><p>');
            text = text.replace(/\n/g, '<br>');
            return '<p>' + text + '</p>';
        }
        
        function addMessage(content, type = 'user') {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            
            if (type === 'assistant') {
                div.innerHTML = '🤖 ' + formatMessage(content);
            } else if (type === 'user') {
                div.innerHTML = content;
            } else {
                div.innerHTML = content;
            }
            
            chatMessages.appendChild(div);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // === FUNCIONES DE UI ===
        function setTaskStatus(status, text) {
            const taskStatus = document.getElementById('taskStatus');
            const statusText = document.getElementById('statusText');
            const statusIcon = document.getElementById('statusIcon');
            
            taskStatus.className = 'task-status ' + status;
            statusText.textContent = text;
            
            switch(status) {
                case 'processing':
                    statusIcon.textContent = '⚙️';
                    break;
                case 'completed':
                    statusIcon.textContent = '✅';
                    break;
                case 'error':
                    statusIcon.textContent = '❌';
                    break;
                default:
                    statusIcon.textContent = '⏱';
            }
        }
        
        function attachFile() {
            // Crear input file dinámico
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.txt,.md,.js,.py,.html,.css,.json,.xml,.csv';
            fileInput.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const content = event.target.result;
                        // Agregar contenido al mensaje
                        const currentMsg = messageInput.value;
                        messageInput.value = currentMsg + (currentMsg ? '\n\n' : '') + 
                            `📎 Archivo adjunto: ${file.name}\n\`\`\`\n${content.substring(0, 2000)}${content.length > 2000 ? '...(truncado)' : ''}\n\`\`\``;
                        messageInput.focus();
                    };
                    reader.readAsText(file);
                }
            };
            fileInput.click();
        }
        
        function toggleTools() {
            alert('🔧 Herramientas disponibles:\n\n' +
                '• Terminal - Ejecutar comandos bash\n' +
                '• Editor - Crear y editar archivos\n' +
                '• Git - Pull, Push, crear PR\n' +
                '• Tareas - Organizar trabajo\n\n' +
                'Escribe tu solicitud y el agente usará las herramientas necesarias.');
        }
        
        async function sendMessage(event) {
            event.preventDefault();
            
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            messageInput.value = '';
            
            // Cambiar estado a procesando
            setTaskStatus('processing', 'Iniciando...');
            
            // Crear elemento para mostrar progreso
            const progressDiv = document.createElement('div');
            progressDiv.className = 'message system streaming-progress';
            progressDiv.innerHTML = '<div class="progress-content">🚀 Iniciando...</div>';
            chatMessages.appendChild(progressDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            try {
                const formData = new FormData();
                formData.append('message', message);
                formData.append('project', currentProject);
                
                // Usar streaming SSE
                const response = await fetch('/api/chat/stream', {
                    method: 'POST',
                    body: formData
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let finalMessage = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const text = decoder.decode(value);
                    const lines = text.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                
                                if (data.type === 'heartbeat') {
                                    continue;
                                }
                                
                                if (data.type === 'done') {
                                    finalMessage = data.message;
                                } else if (data.type === 'error') {
                                    progressDiv.querySelector('.progress-content').innerHTML = 
                                        `❌ Error: ${data.text}`;
                                    setTaskStatus('error', 'Error');
                                } else if (data.type && data.icon && data.text) {
                                    // Actualizar progreso
                                    progressDiv.querySelector('.progress-content').innerHTML = 
                                        `${data.icon} ${data.text}`;
                                    setTaskStatus('processing', data.text.substring(0, 30) + '...');
                                    chatMessages.scrollTop = chatMessages.scrollHeight;
                                }
                            } catch (e) {
                                // Ignorar líneas mal formadas
                            }
                        }
                    }
                }
                
                // Remover progreso y mostrar mensaje final
                progressDiv.remove();
                
                if (finalMessage) {
                    addMessage(finalMessage, 'assistant');
                    setTaskStatus('completed', 'Tarea completada');
                    setTimeout(() => setTaskStatus('', 'Esperando tarea.'), 3000);
                }
                
            } catch (error) {
                progressDiv.remove();
                addMessage('Error de conexión: ' + error.message, 'error');
                setTaskStatus('error', 'Error de conexión');
            }
        }
