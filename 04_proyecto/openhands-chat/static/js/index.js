        // === ESTADO GLOBAL ===
        let currentProject = '';
        let selectedRepo = null;
        let repos = [];
        let currentView = 'chat';
        let codeServerLoaded = false;
        // isMainProject viene del servidor (template)
        
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
            
            // Configurar handlers del iframe de app
            setupAppFrameHandlers();
            
            // Iniciar polling para detectar app servers
            startAppServerPolling();
            
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
                    
                    // PRE-INICIAR servidores para el nuevo chat (como OpenHands)
                    fetch('/api/code-server/prestart', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ conversation_id: data.conversation_id })
                    }).catch(() => {});
                    
                    fetch('/api/app-server/prestart', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ conversation_id: data.conversation_id })
                    }).catch(() => {});
                    
                    // Mostrar tabs y actualizar git bar
                    showCodeTabs(selectedRepo.name);
                    updateGitBar(selectedRepo.owner, selectedRepo.name, branchSelect.value);
                    codeServerLoaded = false;
                    browserLoaded = false;
                    appServerPort = null;
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
            browserLoaded = false; // Reset navegador también
            appServerPort = null; // Reset app server
            clearTerminal(); // Limpiar terminal para nueva conversación
            
            // Resetear vista de aplicación
            const appPlaceholder = document.getElementById('appPlaceholder');
            const appFrame = document.getElementById('appFrame');
            if (appPlaceholder) appPlaceholder.style.display = 'flex';
            if (appFrame) appFrame.style.display = 'none';
            
            // PRE-INICIAR code-server y app-server en background (como OpenHands)
            // Así cuando el usuario haga clic en <> o 🌐, ya estarán listos
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
            
            // Actualizar barra de Git
            if (repoOwner && repoName) {
                updateGitBar(repoOwner, repoName, branch);
                // Actualizar rama real desde el workspace (puede ser diferente a la DB)
                refreshBranchInfo(convId);
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
            
            // Actualizar barra de git con links clickeables
            const repoLink = document.getElementById('gitRepoLink');
            const branchLink = document.getElementById('gitBranchLink');
            
            if (repoFullName) {
                document.getElementById('gitRepoName').textContent = repoFullName;
                if (repoLink) {
                    repoLink.href = `https://github.com/${repoFullName}`;
                    repoLink.style.display = 'flex';
                }
            } else {
                document.getElementById('gitRepoName').textContent = projectName || '';
                if (repoLink) {
                    repoLink.href = '#';
                    repoLink.style.display = projectName ? 'flex' : 'none';
                }
            }
            
            if (branch && branch !== '') {
                document.getElementById('gitBranchName').textContent = branch;
                if (branchLink) {
                    branchLink.href = repoFullName ? `https://github.com/${repoFullName}/tree/${branch}` : '#';
                    branchLink.style.display = 'flex';
                }
            } else {
                if (branchLink) {
                    branchLink.style.display = 'none';
                }
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
        
        // === TABS CHAT/CÓDIGO/TERMINAL ===
        let browserLoaded = false;
        
        function switchView(view) {
            currentView = view;
            const appView = document.getElementById('appView');
            const codeViewRight = document.getElementById('codeViewRight');
            const browserView = document.getElementById('browserView');
            const terminalView = document.getElementById('terminalView');
            const tabChat = document.getElementById('tabChat');
            const tabCode = document.getElementById('tabCode');
            const tabApp = document.getElementById('tabApp');
            const tabBrowser = document.getElementById('tabBrowser');
            const tabTerminal = document.getElementById('tabTerminal');
            
            // Resetear todos los tabs
            tabChat.classList.remove('active');
            tabCode.classList.remove('active');
            tabApp.classList.remove('active');
            if (tabBrowser) tabBrowser.classList.remove('active');
            if (tabTerminal) tabTerminal.classList.remove('active');
            
            // Ocultar todas las vistas
            appView.style.display = 'none';
            codeViewRight.style.display = 'none';
            if (browserView) browserView.style.display = 'none';
            if (terminalView) terminalView.style.display = 'none';
            
            if (view === 'chat') {
                // Chat - no muestra panel derecho especial
                appView.style.display = 'block';
                tabChat.classList.add('active');
            } else if (view === 'app') {
                // Aplicación - para apps dinámicas que el agente inicia
                appView.style.display = 'block';
                tabApp.classList.add('active');
                // Verificar si ya hay un servidor corriendo
                checkAppServer();
            } else if (view === 'code') {
                codeViewRight.style.display = 'block';
                tabCode.classList.add('active');
                if (!codeServerLoaded) {
                    startCodeServer();
                }
            } else if (view === 'browser') {
                // Navegador - Screenshots del browser (como OpenHands)
                browserView.style.display = 'flex';
                if (tabBrowser) tabBrowser.classList.add('active');
                if (!browserLoaded) {
                    loadBrowserScreenshot();
                }
            } else if (view === 'terminal') {
                // Terminal (solo lectura) - como OpenHands
                if (terminalView) {
                    terminalView.style.display = 'flex';
                    tabTerminal.classList.add('active');
                    // Inicializar xterm si no está listo
                    setTimeout(() => {
                        initXterm();
                        if (xtermFitAddon) xtermFitAddon.fit();
                    }, 100);
                }
            }
        }
        
        // === TERMINAL con xterm.js (igual que OpenHands) ===
        let xterm = null;
        let xtermFitAddon = null;
        let xtermInitialized = false;
        
        function initXterm() {
            if (xtermInitialized || !window.Terminal) return;
            
            const container = document.getElementById('xtermContainer');
            if (!container) return;
            
            // Crear terminal con misma config que OpenHands
            xterm = new window.Terminal({
                fontFamily: "Menlo, Monaco, 'Courier New', monospace",
                fontSize: 14,
                scrollback: 10000,
                scrollSensitivity: 1,
                fastScrollSensitivity: 5,
                disableStdin: true,  // Solo lectura
                cursorBlink: false,
                cursorStyle: 'underline',
                theme: {
                    background: '#1e1e1e',
                    foreground: '#d4d4d4',
                    cursor: '#d4d4d4',
                    cursorAccent: '#1e1e1e',
                    selectionBackground: '#264f78',
                    black: '#1e1e1e',
                    red: '#f48771',
                    green: '#4ec9b0',
                    yellow: '#dcdcaa',
                    blue: '#569cd6',
                    magenta: '#c586c0',
                    cyan: '#4ec9b0',
                    white: '#d4d4d4',
                    brightBlack: '#808080',
                    brightRed: '#f48771',
                    brightGreen: '#4ec9b0',
                    brightYellow: '#dcdcaa',
                    brightBlue: '#569cd6',
                    brightMagenta: '#c586c0',
                    brightCyan: '#4ec9b0',
                    brightWhite: '#ffffff'
                }
            });
            
            // FitAddon para ajustar tamaño
            if (window.FitAddon) {
                xtermFitAddon = new window.FitAddon.FitAddon();
                xterm.loadAddon(xtermFitAddon);
            }
            
            xterm.open(container);
            xterm.write('\x1b[?25l');  // Ocultar cursor
            
            // Ajustar tamaño
            if (xtermFitAddon) {
                setTimeout(() => xtermFitAddon.fit(), 100);
            }
            
            // Resize observer
            const resizeObserver = new ResizeObserver(() => {
                if (xtermFitAddon && container.offsetWidth > 0 && container.offsetHeight > 0) {
                    requestAnimationFrame(() => xtermFitAddon.fit());
                }
            });
            resizeObserver.observe(container);
            
            xtermInitialized = true;
            console.log('xterm.js inicializado');
        }
        
        function addTerminalCommand(command) {
            if (!xterm) initXterm();
            if (!xterm) return;
            
            // Escribir prompt y comando en verde
            xterm.writeln('\x1b[36m$\x1b[0m \x1b[32m' + command + '\x1b[0m');
        }
        
        function addTerminalOutput(output, isError = false) {
            if (!xterm || !output) return;
            
            // Limpiar output (quitar info de Python Interpreter si existe)
            let cleanOutput = output;
            const pythonIdx = cleanOutput.indexOf('[Python Interpreter:');
            if (pythonIdx > 0) {
                cleanOutput = cleanOutput.substring(0, pythonIdx).trim();
            }
            
            // Color rojo para errores, blanco para output normal
            const color = isError ? '\x1b[31m' : '\x1b[0m';
            
            // Escribir cada línea
            const lines = cleanOutput.split('\n');
            lines.forEach(line => {
                if (line.trim()) {
                    xterm.writeln(color + line + '\x1b[0m');
                }
            });
        }
        
        function scrollTerminalToBottom() {
            if (xterm) {
                xterm.scrollToBottom();
            }
        }
        
        function clearTerminal() {
            if (xterm) {
                xterm.clear();
            }
        }
        
        // === NAVEGADOR (Browser Screenshots - como OpenHands) ===
        let currentBrowserUrl = '';
        let currentScreenshot = null;
        
        async function loadBrowserScreenshot() {
            // Cargar screenshot del navegador desde la API
            try {
                const resp = await fetch(`/api/browser/screenshot?conversation_id=${currentConversationId}`);
                const data = await resp.json();
                
                if (data.screenshot) {
                    showBrowserScreenshot(data.url, data.screenshot);
                } else {
                    showBrowserEmpty();
                }
            } catch (e) {
                console.log('No browser screenshot available');
                showBrowserEmpty();
            }
            browserLoaded = true;
        }
        
        function showBrowserScreenshot(url, screenshotBase64) {
            const urlInput = document.getElementById('browserUrl');
            const screenshot = document.getElementById('browserScreenshot');
            const empty = document.getElementById('browserEmpty');
            
            currentBrowserUrl = url;
            currentScreenshot = screenshotBase64;
            
            urlInput.value = url || '';
            
            // Mostrar screenshot
            const imgSrc = screenshotBase64.startsWith('data:image/')
                ? screenshotBase64
                : `data:image/png;base64,${screenshotBase64}`;
            screenshot.src = imgSrc;
            screenshot.style.display = 'block';
            empty.style.display = 'none';
        }
        
        function showBrowserEmpty() {
            const urlInput = document.getElementById('browserUrl');
            const screenshot = document.getElementById('browserScreenshot');
            const empty = document.getElementById('browserEmpty');
            
            urlInput.value = '';
            screenshot.style.display = 'none';
            empty.style.display = 'flex';
            empty.style.flexDirection = 'column';
            empty.style.alignItems = 'center';
            empty.style.justifyContent = 'center';
            empty.style.height = '100%';
        }
        
        function refreshBrowser() {
            browserLoaded = false;
            loadBrowserScreenshot();
        }
        
        // Función para actualizar screenshot desde el agente (vía WebSocket)
        function updateBrowserScreenshot(url, screenshot) {
            currentBrowserUrl = url;
            currentScreenshot = screenshot;
            if (currentView === 'browser') {
                showBrowserScreenshot(url, screenshot);
            }
        }
        
        // === APLICACIÓN (Port Forwarding dinámico como OpenHands Cloud) ===
        let appServerPort = null;
        
        async function checkAppServer() {
            // Detectar puerto activo automáticamente (como OpenHands Cloud)
            try {
                const resp = await fetch('/api/app-server/active-port?conversation_id=' + currentConversationId);
                const data = await resp.json();
                
                // Si hay un servidor activo en cualquier puerto
                if (data.status === 'active' && data.port) {
                    showAppInIframe(data.port);
                    return true;
                } else {
                    // No hay servidor - mostrar placeholder
                    hideAppIframe();
                }
            } catch (e) {
                console.log('No app server detected');
                hideAppIframe();
            }
            return false;
        }
        
        function hideAppIframe() {
            // Ocultar iframe y mostrar placeholder cuando no hay servidor
            const placeholder = document.getElementById('appPlaceholder');
            const frame = document.getElementById('appFrame');
            const urlInput = document.getElementById('appUrl');
            
            if (appServerPort !== null) {
                appServerPort = null;
                placeholder.style.display = 'flex';
                frame.style.display = 'none';
                frame.src = 'about:blank';
                urlInput.value = 'http://localhost:PORT';
                console.log('App server stopped - showing placeholder');
            }
        }
        
        // Configurar handlers del iframe al cargar la página
        function setupAppFrameHandlers() {
            const frame = document.getElementById('appFrame');
            if (!frame) return;
            
            // Handler cuando el iframe termina de cargar
            frame.onload = function() {
                console.log('App iframe loaded successfully');
                // Marcar como cargado
                frame.dataset.loaded = 'true';
            };
            
            // Handler de error - reintentar automáticamente
            frame.onerror = function() {
                console.log('App iframe error - will retry on next poll');
                frame.dataset.loaded = 'false';
            };
            
            // Prevenir que clics en el iframe causen scroll en la página padre
            // Interceptar cambios de hash en la ventana principal
            window.addEventListener('hashchange', (e) => {
                // Si el hash cambió, resetear scroll
                window.scrollTo(0, 0);
                document.documentElement.scrollTop = 0;
                document.body.scrollTop = 0;
            });
            
            // También escuchar scroll en window y resetearlo
            let scrollLocked = false;
            window.addEventListener('scroll', (e) => {
                if (!scrollLocked && (window.scrollY > 0 || document.documentElement.scrollTop > 0)) {
                    scrollLocked = true;
                    window.scrollTo(0, 0);
                    document.documentElement.scrollTop = 0;
                    document.body.scrollTop = 0;
                    setTimeout(() => { scrollLocked = false; }, 100);
                }
            });
        }
        
        function showAppInIframe(port) {
            const placeholder = document.getElementById('appPlaceholder');
            const frame = document.getElementById('appFrame');
            const urlInput = document.getElementById('appUrl');
            const copyBtn = document.getElementById('copyUrlBtn');
            
            // Solo actualizar si el puerto cambió
            if (appServerPort !== port) {
                appServerPort = port;
                placeholder.style.display = 'none';
                frame.style.display = 'block';
                // Agregar timestamp para evitar caché
                frame.src = `/api/app-server/app-preview/?conversation_id=${currentConversationId}&_t=${Date.now()}`;
                urlInput.value = `http://localhost:${port}`;
                // Mostrar botón de copiar URL externa
                if (copyBtn) copyBtn.style.display = 'inline-block';
                console.log(`App server detected on port ${port}`);
            }
        }
        
        function refreshApp() {
            const frame = document.getElementById('appFrame');
            if (appServerPort) {
                // Forzar recarga con timestamp para evitar caché
                const baseUrl = `/api/app-server/app-preview/?conversation_id=${currentConversationId}`;
                frame.src = `${baseUrl}&_t=${Date.now()}`;
            } else {
                checkAppServer();
            }
        }
        
        // Copiar URL externa para compartir
        function copyExternalUrl() {
            if (!currentConversationId) {
                showNotification('No hay conversación activa', 'error');
                return;
            }
            
            // Construir URL externa completa
            const baseUrl = window.location.origin;
            const externalUrl = `${baseUrl}/api/app-server/app-preview/?conversation_id=${currentConversationId}`;
            
            navigator.clipboard.writeText(externalUrl).then(() => {
                showNotification('✅ URL copiada al portapapeles', 'success');
                
                // Feedback visual en el botón
                const btn = document.getElementById('copyUrlBtn');
                const originalText = btn.textContent;
                btn.textContent = '✓';
                setTimeout(() => { btn.textContent = originalText; }, 1500);
            }).catch(err => {
                // Fallback para navegadores sin clipboard API
                const textArea = document.createElement('textarea');
                textArea.value = externalUrl;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showNotification('✅ URL copiada', 'success');
            });
        }
        
        // Obtener URL externa para mostrar en chat
        function getExternalAppUrl() {
            if (!currentConversationId) return null;
            return `${window.location.origin}/api/app-server/app-preview/?conversation_id=${currentConversationId}`;
        }
        
        // Polling para detectar cuando el agente inicia un servidor
        // Siempre verifica por si el agente inicia un servidor nuevo
        let appServerPollingActive = false;
        function startAppServerPolling() {
            if (appServerPollingActive) return; // Evitar duplicados
            appServerPollingActive = true;
            
            setInterval(async () => {
                // Siempre verificar cuando estamos en vista app
                if (currentView === 'app' && document.visibilityState === 'visible') {
                    await checkAppServer();
                }
            }, 3000);
        }
        
        async function startCodeServer() {
            const loading = document.getElementById('codeLoadingRight');
            const frame = document.getElementById('codeServerFrameRight');
            
            loading.style.display = 'flex';
            loading.innerHTML = '<div class="loading-spinner"></div><p>Cargando VS Code...</p>';
            frame.style.display = 'none';
            
            // Función para mostrar el iframe cuando cargue
            const showFrameOnLoad = () => {
                frame.onload = () => {
                    // Esperar un poco más para que VS Code renderice completamente
                    setTimeout(() => {
                        frame.style.display = 'block';
                        loading.style.display = 'none';
                        codeServerLoaded = true;
                    }, 800);
                };
            };
            
            try {
                // Primero verificar si ya está corriendo (por el prestart)
                const statusResp = await fetch('/api/code-server/status');
                const statusData = await statusResp.json();
                
                if (statusData.status === 'running' && statusData.port) {
                    // Ya está corriendo, cargar iframe
                    showFrameOnLoad();
                    frame.src = '/code-server/';
                    return;
                }
                
                // Si no está corriendo, iniciarlo
                const response = await fetch('/api/code-server/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ conversation_id: currentConversationId })
                });
                
                const data = await response.json();
                
                if (response.status === 403) {
                    loading.innerHTML = '<p>⚠️ El editor de código no está disponible para el proyecto principal (test03)</p>';
                    return;
                }
                
                if (response.status === 404) {
                    loading.innerHTML = `
                        <p>📁 El proyecto no está clonado localmente</p>
                        <p style="font-size: 0.9em; color: #8b949e;">Haz Pull para clonar el repositorio</p>
                    `;
                    return;
                }
                
                if (data.status === 'started' || data.status === 'running') {
                    showFrameOnLoad();
                    frame.src = '/code-server/';
                } else {
                    loading.innerHTML = `<p>❌ ${data.message || data.error || 'No se pudo iniciar el editor'}</p>`;
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
            const rightPanel = document.querySelector('.chat-right-panel');
            const leftPanel = document.querySelector('.chat-left-panel');
            
            // Usar la variable del servidor si está definida, sino detectar por nombre
            const isTest03 = (typeof isMainProject !== 'undefined' && isMainProject) || 
                             (repoName && repoName.toLowerCase().includes('test03'));
            
            if (isTest03) {
                // Ocultar panel derecho completo para test03
                if (viewTabs) viewTabs.style.display = 'none';
                if (rightPanel) rightPanel.style.display = 'none';
                if (leftPanel) leftPanel.style.flex = '1';
            } else {
                if (viewTabs) viewTabs.style.display = 'flex';
                if (rightPanel) rightPanel.style.display = 'flex';
                if (leftPanel) leftPanel.style.flex = '';
            }
        }
        
        function showHelp() {
            alert('🤖 OpenHands Chat\n\n1. Configura tu API key en Configuración\n2. Conecta tu cuenta de GitHub\n3. Selecciona un repositorio o empieza desde cero\n4. ¡Empieza a construir!');
        }
        
        // === ACCIONES GIT ===
        let currentGitInfo = { owner: '', repo: '', branch: 'main' };
        
        function updateGitBar(owner, repo, branch) {
            currentGitInfo = { owner, repo, branch: branch || 'main' };
            const repoFullName = `${owner}/${repo}`;
            const branchName = branch || 'main';
            
            // Actualizar texto
            document.getElementById('gitRepoName').textContent = repoFullName;
            document.getElementById('gitBranchName').textContent = branchName;
            
            // Actualizar URLs de los links (clickeables como OpenHands)
            const repoLink = document.getElementById('gitRepoLink');
            const branchLink = document.getElementById('gitBranchLink');
            
            if (repoLink) {
                repoLink.href = `https://github.com/${repoFullName}`;
            }
            if (branchLink) {
                branchLink.href = `https://github.com/${repoFullName}/tree/${branchName}`;
            }
        }
        
        // SVG icons para los botones Git
        const gitIcons = {
            pull: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M7.47 10.78a.75.75 0 001.06 0l3.75-3.75a.75.75 0 00-1.06-1.06L8.75 8.44V1.75a.75.75 0 00-1.5 0v6.69L4.78 5.97a.75.75 0 00-1.06 1.06l3.75 3.75zM3.75 13a.75.75 0 000 1.5h8.5a.75.75 0 000-1.5h-8.5z"/></svg>',
            push: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M8.53 1.22a.75.75 0 00-1.06 0L3.72 4.97a.75.75 0 001.06 1.06l2.47-2.47v6.69a.75.75 0 001.5 0V3.56l2.47 2.47a.75.75 0 101.06-1.06L8.53 1.22zM3.75 13a.75.75 0 000 1.5h8.5a.75.75 0 000-1.5h-8.5z"/></svg>',
            pr: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/></svg>',
            loading: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" class="spin"><path d="M8 0a8 8 0 100 16A8 8 0 008 0zm0 1.5a6.5 6.5 0 110 13 6.5 6.5 0 010-13z" opacity="0.3"/><path d="M8 0a8 8 0 018 8h-1.5A6.5 6.5 0 008 1.5V0z"/></svg>'
        };
        
        // Git buttons - EXACTAMENTE como OpenHands
        function gitPull() {
            // Prompt EXACTO de OpenHands
            const pullPrompt = "Please pull the latest code from the repository.";
            setMessageInputValue(pullPrompt);
            sendMessage(new Event('submit'));
        }
        
        function gitPush() {
            // Prompt EXACTO de OpenHands
            const pushPrompt = "Please push the changes to a remote branch on GitHub, but do NOT create a Pull Request. " +
                "Check your current branch name first - if it's main, master, deploy, or another common default branch name, " +
                "create a new branch with a descriptive name related to your changes. " +
                "Otherwise, use the exact SAME branch name as the one you are currently on.";
            setMessageInputValue(pushPrompt);
            sendMessage(new Event('submit'));
        }
        
        function createPR() {
            // Prompt EXACTO de OpenHands
            const prPrompt = "Please push the changes to GitHub and open a Pull Request. " +
                "If you're on a default branch (e.g., main, master, deploy), create a new branch with a descriptive name " +
                "otherwise use the current branch. " +
                "If a Pull Request template exists in the repository, please follow it when creating the PR description.";
            setMessageInputValue(prPrompt);
            sendMessage(new Event('submit'));
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
            
            // Usar marked.js para renderizar markdown completo
            // Incluye: tablas, listas, código, negritas, links, etc.
            try {
                // Configurar marked con highlight.js para syntax highlighting
                if (typeof marked !== 'undefined') {
                    marked.setOptions({
                        breaks: true,  // Convertir \n a <br>
                        gfm: true,     // GitHub Flavored Markdown (tablas, etc)
                        highlight: function(code, lang) {
                            if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                                try {
                                    return hljs.highlight(code, { language: lang }).value;
                                } catch (e) {}
                            }
                            // Auto-detect language
                            if (typeof hljs !== 'undefined') {
                                try {
                                    return hljs.highlightAuto(code).value;
                                } catch (e) {}
                            }
                            return code;
                        }
                    });
                    
                    const html = marked.parse(text);
                    
                    // Aplicar highlight a bloques de código después del render
                    setTimeout(() => {
                        document.querySelectorAll('pre code:not(.hljs)').forEach((block) => {
                            if (typeof hljs !== 'undefined') {
                                hljs.highlightElement(block);
                            }
                        });
                    }, 0);
                    
                    return html;
                }
            } catch (e) {
                console.error('Error rendering markdown:', e);
            }
            
            // Fallback básico si marked no está disponible
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
        
        // Agregar mensaje con imágenes adjuntas
        function addMessageWithImages(content, type, images = []) {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            
            let html = '';
            
            // Mostrar imágenes primero
            if (images.length > 0) {
                html += '<div class="message-images">';
                images.forEach(img => {
                    html += `<img src="${img.dataUrl}" alt="${img.name}" class="message-image" onclick="showImageFullscreen('${img.dataUrl}')">`;
                });
                html += '</div>';
            }
            
            // Luego el texto
            if (content) {
                if (type === 'assistant') {
                    html += '🤖 ' + formatMessage(content);
                } else {
                    html += content;
                }
            }
            
            div.innerHTML = html;
            chatMessages.appendChild(div);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Mostrar imagen en pantalla completa
        function showImageFullscreen(src) {
            const overlay = document.createElement('div');
            overlay.className = 'image-fullscreen-overlay';
            overlay.innerHTML = `
                <img src="${src}" class="fullscreen-image">
                <button class="close-fullscreen" onclick="this.parentElement.remove()">×</button>
            `;
            overlay.onclick = (e) => {
                if (e.target === overlay) overlay.remove();
            };
            document.body.appendChild(overlay);
        }
        
        // === FUNCIONES DE UI ===
        
        // Estado del agente (como OpenHands)
        let currentAgentState = 'idle'; // idle, running, paused, loading, error
        
        function setTaskStatus(status, text) {
            const taskStatus = document.getElementById('taskStatus');
            const statusText = document.getElementById('statusText');
            
            taskStatus.className = 'task-status ' + status;
            statusText.textContent = text;
            
            // Mapear status a agent state
            switch(status) {
                case 'processing':
                    setAgentState('running');
                    break;
                case 'completed':
                    setAgentState('idle');
                    break;
                case 'error':
                    setAgentState('error');
                    break;
                default:
                    setAgentState('idle');
            }
        }
        
        // Task Tracker UI - Mostrar lista de tareas del agente
        let currentTasks = [];
        
        function updateTaskTrackerUI(tasks) {
            if (!tasks || tasks.length === 0) return;
            
            currentTasks = tasks;
            
            // Buscar o crear el contenedor de tareas
            let taskContainer = document.getElementById('taskTrackerContainer');
            if (!taskContainer) {
                taskContainer = document.createElement('div');
                taskContainer.id = 'taskTrackerContainer';
                taskContainer.className = 'task-tracker-container';
                
                // Insertar después del header del chat o al inicio del panel derecho
                const rightPanel = document.querySelector('.right-panel');
                if (rightPanel) {
                    rightPanel.insertBefore(taskContainer, rightPanel.firstChild);
                }
            }
            
            // Renderizar tareas
            const taskHTML = tasks.map((task, idx) => {
                const status = task.status || 'todo';
                const title = task.title || `Tarea ${idx + 1}`;
                const notes = task.notes || '';
                
                let statusIcon = '○';  // todo
                let statusClass = 'todo';
                if (status === 'in_progress') {
                    statusIcon = '◐';
                    statusClass = 'in-progress';
                } else if (status === 'done') {
                    statusIcon = '✓';
                    statusClass = 'done';
                }
                
                return `
                    <div class="task-item ${statusClass}">
                        <span class="task-status-icon">${statusIcon}</span>
                        <span class="task-title">${title}</span>
                        ${notes ? `<span class="task-notes">${notes}</span>` : ''}
                    </div>
                `;
            }).join('');
            
            taskContainer.innerHTML = `
                <div class="task-tracker-header">
                    <span class="task-tracker-icon">📋</span>
                    <span class="task-tracker-title">Tareas</span>
                    <span class="task-count">${tasks.filter(t => t.status === 'done').length}/${tasks.length}</span>
                </div>
                <div class="task-tracker-list">
                    ${taskHTML}
                </div>
            `;
            
            taskContainer.style.display = 'block';
        }
        
        function hideTaskTracker() {
            const container = document.getElementById('taskTrackerContainer');
            if (container) {
                container.style.display = 'none';
            }
        }
        
        // Actualizar el icono según el estado del agente (como OpenHands)
        function setAgentState(state) {
            currentAgentState = state;
            
            const iconClock = document.getElementById('iconClock');
            const iconPause = document.getElementById('iconPause');
            const iconPlay = document.getElementById('iconPlay');
            const iconLoading = document.getElementById('iconLoading');
            const btn = document.getElementById('agentControlBtn');
            
            // Ocultar todos los iconos
            iconClock.style.display = 'none';
            iconPause.style.display = 'none';
            iconPlay.style.display = 'none';
            iconLoading.style.display = 'none';
            
            // Remover clase clickable por defecto
            btn.classList.remove('clickable');
            btn.title = 'Estado del agente';
            
            switch(state) {
                case 'running':
                    iconPause.style.display = 'block';
                    btn.classList.add('clickable');
                    btn.title = 'Pausar agente';
                    break;
                case 'paused':
                case 'stopped':
                    iconPlay.style.display = 'block';
                    btn.classList.add('clickable');
                    btn.title = 'Reanudar agente';
                    break;
                case 'loading':
                    iconLoading.style.display = 'flex';
                    break;
                case 'error':
                    iconClock.style.display = 'block';
                    break;
                case 'idle':
                default:
                    iconClock.style.display = 'block';
                    break;
            }
        }
        
        // Toggle del estado del agente (pause/resume)
        window.toggleAgentState = function() {
            if (currentAgentState === 'running') {
                // Pausar el agente
                pauseAgent();
            } else if (currentAgentState === 'paused' || currentAgentState === 'stopped') {
                // Reanudar el agente
                resumeAgent();
            }
            // Si está en idle, loading o error, no hacer nada
        };
        
        // Pausar el agente
        async function pauseAgent() {
            if (!currentConversationId) return;
            
            setAgentState('loading');
            
            try {
                const response = await fetch(`/api/conversations/${currentConversationId}/pause`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.ok) {
                    setAgentState('paused');
                    document.getElementById('statusText').textContent = 'Agente pausado.';
                } else {
                    setAgentState('running');
                }
            } catch (e) {
                console.error('Error pausando agente:', e);
                setAgentState('running');
            }
        }
        
        // Reanudar el agente
        async function resumeAgent() {
            if (!currentConversationId) return;
            
            setAgentState('loading');
            
            try {
                const response = await fetch(`/api/conversations/${currentConversationId}/resume`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.ok) {
                    setAgentState('running');
                    document.getElementById('statusText').textContent = 'Agente ejecutándose...';
                } else {
                    setAgentState('paused');
                }
            } catch (e) {
                console.error('Error reanudando agente:', e);
                setAgentState('paused');
            }
        }
        
        // === MANEJO DE ARCHIVOS E IMÁGENES ===
        let attachedFiles = []; // Array de {file, dataUrl, type}
        
        function attachFile() {
            document.getElementById('fileInput').click();
        }
        
        // Setup file input change handler
        document.addEventListener('DOMContentLoaded', () => {
            const fileInput = document.getElementById('fileInput');
            const messageInputEl = document.getElementById('messageInput');
            const chatInputContainer = document.querySelector('.chat-input-container');
            
            if (fileInput) {
                fileInput.addEventListener('change', handleFileSelect);
            }
            
            if (messageInputEl) {
                // Paste handler
                messageInputEl.addEventListener('paste', handlePaste);
                
                // Enter key handler
                messageInputEl.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        document.getElementById('chatForm').dispatchEvent(new Event('submit'));
                    }
                });
            }
            
            if (chatInputContainer) {
                // Drag and drop handlers
                chatInputContainer.addEventListener('dragover', handleDragOver);
                chatInputContainer.addEventListener('dragleave', handleDragLeave);
                chatInputContainer.addEventListener('drop', handleDrop);
            }
        });
        
        function handleFileSelect(e) {
            const files = Array.from(e.target.files || []);
            processFiles(files);
            e.target.value = ''; // Reset input
        }
        
        function handlePaste(e) {
            const items = e.clipboardData?.items;
            if (!items) return;
            
            const files = [];
            for (const item of items) {
                if (item.type.startsWith('image/')) {
                    const file = item.getAsFile();
                    if (file) files.push(file);
                }
            }
            
            if (files.length > 0) {
                e.preventDefault();
                processFiles(files);
            }
            // Si no hay imágenes, deja que pegue texto normal
        }
        
        function handleDragOver(e) {
            e.preventDefault();
            e.currentTarget.classList.add('drag-over');
        }
        
        function handleDragLeave(e) {
            e.preventDefault();
            e.currentTarget.classList.remove('drag-over');
        }
        
        function handleDrop(e) {
            e.preventDefault();
            e.currentTarget.classList.remove('drag-over');
            const files = Array.from(e.dataTransfer?.files || []);
            processFiles(files);
        }
        
        function processFiles(files) {
            files.forEach(file => {
                const reader = new FileReader();
                reader.onload = (event) => {
                    const dataUrl = event.target.result;
                    const isImage = file.type.startsWith('image/');
                    
                    attachedFiles.push({
                        file: file,
                        dataUrl: dataUrl,
                        type: isImage ? 'image' : 'text',
                        name: file.name
                    });
                    
                    updateAttachedFilesUI();
                };
                
                if (file.type.startsWith('image/')) {
                    reader.readAsDataURL(file);
                } else {
                    reader.readAsText(file);
                }
            });
        }
        
        function updateAttachedFilesUI() {
            const container = document.getElementById('attachedImages');
            if (!container) return;
            
            container.innerHTML = '';
            
            attachedFiles.forEach((item, index) => {
                const div = document.createElement('div');
                div.className = 'attached-image-item';
                
                if (item.type === 'image') {
                    div.innerHTML = `
                        <img src="${item.dataUrl}" alt="${item.name}">
                        <button class="remove-image" onclick="removeAttachedFile(${index})">×</button>
                    `;
                } else {
                    div.innerHTML = `
                        <div style="padding: 8px; background: #21262d; font-size: 12px; color: #8b949e;">
                            📎 ${item.name}
                        </div>
                        <button class="remove-image" onclick="removeAttachedFile(${index})">×</button>
                    `;
                }
                
                container.appendChild(div);
            });
        }
        
        function removeAttachedFile(index) {
            attachedFiles.splice(index, 1);
            updateAttachedFilesUI();
        }
        
        function clearAttachedFiles() {
            attachedFiles = [];
            updateAttachedFilesUI();
        }
        
        // Helper to get message from contenteditable
        function getMessageInputValue() {
            const el = document.getElementById('messageInput');
            return el ? el.textContent.trim() : '';
        }
        
        function setMessageInputValue(value) {
            const el = document.getElementById('messageInput');
            if (el) el.textContent = value;
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
            
            const message = getMessageInputValue();
            const hasImages = attachedFiles.some(f => f.type === 'image');
            const hasTextFiles = attachedFiles.some(f => f.type === 'text');
            
            if (!message && !hasImages && !hasTextFiles) return;
            
            // Construir mensaje completo con archivos de texto
            let fullMessage = message;
            attachedFiles.filter(f => f.type === 'text').forEach(f => {
                fullMessage += (fullMessage ? '\n\n' : '') + 
                    `📎 Archivo adjunto: ${f.name}\n\`\`\`\n${f.dataUrl.substring(0, 2000)}${f.dataUrl.length > 2000 ? '...(truncado)' : ''}\n\`\`\``;
            });
            
            // Mostrar mensaje del usuario (con thumbnails de imágenes)
            addMessageWithImages(fullMessage, 'user', attachedFiles.filter(f => f.type === 'image'));
            
            // Limpiar input y archivos adjuntos
            setMessageInputValue('');
            const currentImages = [...attachedFiles.filter(f => f.type === 'image')]; // Guardar copia para enviar
            clearAttachedFiles();
            
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
                formData.append('message', fullMessage);
                formData.append('project', currentProject);
                
                // Agregar imágenes como base64
                if (currentImages.length > 0) {
                    formData.append('images', JSON.stringify(currentImages.map(img => ({
                        name: img.name,
                        dataUrl: img.dataUrl
                    }))));
                }
                
                // Usar streaming SSE
                const response = await fetch('/api/chat/stream', {
                    method: 'POST',
                    body: formData
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let finalMessage = '';
                
                // STREAMING DE TOKENS - Variables para acumular respuesta en tiempo real
                let streamingText = '';
                let streamingDiv = null;  // Elemento donde se muestra el texto en tiempo real
                
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
                                
                                // STREAMING DE TOKENS - Mostrar texto en tiempo real
                                if (data.type === 'token' && data.content) {
                                    streamingText += data.content;
                                    
                                    // Crear elemento de streaming si no existe
                                    if (!streamingDiv) {
                                        streamingDiv = document.createElement('div');
                                        streamingDiv.className = 'message assistant streaming';
                                        streamingDiv.innerHTML = '<div class="message-content"></div>';
                                        chatMessages.appendChild(streamingDiv);
                                    }
                                    
                                    // Actualizar contenido con el texto acumulado
                                    const contentEl = streamingDiv.querySelector('.message-content');
                                    contentEl.innerHTML = marked.parse(streamingText);
                                    chatMessages.scrollTop = chatMessages.scrollHeight;
                                    
                                    // Actualizar status
                                    setTaskStatus('processing', 'Escribiendo...');
                                    continue;
                                }
                                
                                if (data.type === 'done') {
                                    finalMessage = data.message;
                                    // Si hay streaming activo, usar ese texto
                                    if (streamingText && !finalMessage) {
                                        finalMessage = streamingText;
                                    }
                                } else if (data.type === 'error') {
                                    progressDiv.querySelector('.progress-content').innerHTML = 
                                        `❌ Error: ${data.text}`;
                                    setTaskStatus('error', 'Error');
                                } else if (data.type === 'browser' && data.screenshot) {
                                    // Screenshot del navegador detectado - actualizar vista
                                    progressDiv.querySelector('.progress-content').innerHTML = 
                                        `${data.icon} ${data.text}`;
                                    setTaskStatus('processing', 'Navegando...');
                                    // Refrescar screenshot del navegador
                                    browserLoaded = false;
                                    if (currentView === 'browser') {
                                        loadBrowserScreenshot();
                                    }
                                } else if (data.type === 'terminal_command') {
                                    // Comando ejecutado - agregar a terminal
                                    addTerminalCommand(data.command);
                                } else if (data.type === 'terminal_output') {
                                    // Output del comando - agregar a terminal
                                    const isError = data.exit_code !== 0 || data.stderr;
                                    const output = data.stderr || data.output;
                                    addTerminalOutput(output, isError);
                                } else if (data.type === 'task_tracker_update') {
                                    // Task Tracker - actualizar lista de tareas
                                    updateTaskTrackerUI(data.tasks);
                                    setTaskStatus('processing', 'Actualizando tareas...');
                                } else if (data.type === 'think') {
                                    // Think action - mostrar pensamiento del agente
                                    progressDiv.querySelector('.progress-content').innerHTML = 
                                        `🧠 Pensando: ${data.text.substring(0, 80)}...`;
                                    setTaskStatus('processing', 'Analizando...');
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
                
                // Limpiar div de streaming si existe (se reemplazará por el mensaje final)
                if (streamingDiv) {
                    streamingDiv.remove();
                }
                
                // Remover progreso y mostrar mensaje final
                progressDiv.remove();
                
                if (finalMessage) {
                    addMessage(finalMessage, 'assistant');
                    setTaskStatus('completed', 'Tarea completada');
                    setTimeout(() => setTaskStatus('', 'Esperando tarea.'), 3000);
                    
                    // Actualizar rama si hubo operaciones git
                    if (currentConversationId) {
                        refreshBranchInfo(currentConversationId);
                    }
                }
                
            } catch (error) {
                progressDiv.remove();
                addMessage('Error de conexión: ' + error.message, 'error');
                setTaskStatus('error', 'Error de conexión');
            }
        }
        
        // Actualizar info de rama desde el workspace real
        async function refreshBranchInfo(conversationId) {
            try {
                const response = await fetch(`/api/conversations/${conversationId}/git-status`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.branch) {
                        const branchLink = document.getElementById('gitBranchLink');
                        const branchName = document.getElementById('gitBranchName');
                        if (branchName) {
                            branchName.textContent = data.branch;
                        }
                        if (branchLink && currentGitInfo.owner && currentGitInfo.repo) {
                            branchLink.href = `https://github.com/${currentGitInfo.owner}/${currentGitInfo.repo}/tree/${data.branch}`;
                        }
                        currentGitInfo.branch = data.branch;
                    }
                }
            } catch (e) {
                console.log('No se pudo actualizar info de rama:', e);
            }
        }
