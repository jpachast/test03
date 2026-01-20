        async function togglePassword(inputId = 'api_key') {
            const input = document.getElementById(inputId);
            const btn = event.target;
            
            if (input.type === 'password') {
                // Cargar valor real desde BD
                const endpoint = inputId === 'deepseek_key' ? '/api/settings/deepseek-key' : '/api/settings/api-key';
                try {
                    const resp = await fetch(endpoint);
                    const data = await resp.json();
                    if (data.value) {
                        input.value = data.value;
                        input.type = 'text';
                        btn.textContent = '🙈 Ocultar';
                    }
                } catch (e) {
                    console.error(e);
                }
            } else {
                input.type = 'password';
                input.value = '';
                input.placeholder = '••••••••••••••••';
                btn.textContent = '👁️ Ver';
            }
        }
        
        function showSection(section) {
            // Ocultar todas las secciones
            document.querySelectorAll('.settings-section-content').forEach(el => {
                el.style.display = 'none';
            });
            // Mostrar la seleccionada
            document.getElementById('section-' + section).style.display = 'block';
            
            // Actualizar navegación
            document.querySelectorAll('.settings-nav a').forEach(el => {
                el.classList.remove('active');
            });
            event.target.classList.add('active');
        }
        
        // Cargar estado de GitHub al iniciar
        document.addEventListener('DOMContentLoaded', async () => {
            await checkGitHubStatus();
            
            // Verificar si hay un tab específico en la URL
            const urlParams = new URLSearchParams(window.location.search);
            const tab = urlParams.get('tab');
            if (tab) {
                showSectionDirect(tab);
            }
            
            // También verificar el hash
            if (window.location.hash) {
                const hashTab = window.location.hash.replace('#', '');
                showSectionDirect(hashTab);
            }
        });
        
        function showSectionDirect(section) {
            // Ocultar todas las secciones
            document.querySelectorAll('.settings-section-content').forEach(el => {
                el.style.display = 'none';
            });
            // Mostrar la seleccionada
            const sectionEl = document.getElementById('section-' + section);
            if (sectionEl) {
                sectionEl.style.display = 'block';
            }
            
            // Actualizar navegación
            document.querySelectorAll('.settings-nav a').forEach(el => {
                el.classList.remove('active');
                if (el.getAttribute('href').includes(section)) {
                    el.classList.add('active');
                }
            });
        }
        
        async function checkGitHubStatus() {
            try {
                const response = await fetch('/api/github/status');
                const data = await response.json();
                
                if (data.configured && data.username) {
                    showGitHubConnected(data.username);
                }
            } catch (error) {
                console.error('Error checking GitHub status:', error);
            }
        }
        
        async function connectGitHub() {
            const token = document.getElementById('github_token').value.trim();
            if (!token) {
                alert('Por favor ingresa tu GitHub token');
                return;
            }
            
            try {
                const response = await fetch('/api/github/token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token: token})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showGitHubConnected(data.username, data.avatar_url);
                    alert('✅ GitHub conectado exitosamente');
                } else {
                    alert('Error: ' + (data.error || 'No se pudo conectar'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function disconnectGitHub() {
            if (!confirm('¿Estás seguro de desconectar GitHub?')) return;
            
            try {
                await fetch('/api/github/token', {method: 'DELETE'});
                document.getElementById('githubNotConnected').style.display = 'block';
                document.getElementById('githubConnected').style.display = 'none';
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        function showGitHubConnected(username, avatarUrl) {
            document.getElementById('githubNotConnected').style.display = 'none';
            document.getElementById('githubConnected').style.display = 'flex';
            document.getElementById('githubUsername').textContent = username;
            if (avatarUrl) {
                document.getElementById('githubAvatar').src = avatarUrl;
            } else {
                document.getElementById('githubAvatar').src = `https://github.com/${username}.png`;
            }
        }
        
        // === TAVILY ===
        async function connectTavily() {
            const apiKey = document.getElementById('tavily_api_key').value.trim();
            if (!apiKey) {
                alert('Por favor ingresa tu Tavily API Key');
                return;
            }
            
            try {
                const response = await fetch('/api/settings/tavily', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({api_key: apiKey})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showTavilyConnected();
                    alert('✅ Tavily configurado exitosamente');
                } else {
                    alert('Error: ' + (data.error || 'No se pudo configurar'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function disconnectTavily() {
            if (!confirm('¿Estás seguro de desconectar Tavily?')) return;
            
            try {
                await fetch('/api/settings/tavily', {method: 'DELETE'});
                document.getElementById('tavilyNotConnected').style.display = 'block';
                document.getElementById('tavilyConnected').style.display = 'none';
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        function showTavilyConnected() {
            document.getElementById('tavilyNotConnected').style.display = 'none';
            document.getElementById('tavilyConnected').style.display = 'flex';
        }
        
        // Verificar estado de Tavily al cargar
        async function checkTavilyStatus() {
            try {
                const response = await fetch('/api/settings/tavily');
                const data = await response.json();
                if (data.connected) {
                    showTavilyConnected();
                }
            } catch (error) {
                console.error('Error checking Tavily status:', error);
            }
        }
        
        // ============================================
        // Hetzner Cloud Functions
        // ============================================
        
        async function saveHetznerToken() {
            const token = document.getElementById('hetzner_api_token').value.trim();
            if (!token) {
                alert('Por favor ingresa tu Hetzner API Token');
                return;
            }
            
            try {
                const response = await fetch('/api/settings/hetzner', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token: token})
                });
                
                if (response.ok) {
                    const data = await response.json();
                    showHetznerConnected(data.servers || 0);
                    alert('✅ Hetzner configurado exitosamente');
                } else {
                    const error = await response.json();
                    alert('Error: ' + (error.detail || 'Token inválido'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function disconnectHetzner() {
            if (!confirm('¿Estás seguro de desconectar Hetzner?')) return;
            
            try {
                await fetch('/api/settings/hetzner', {method: 'DELETE'});
                document.getElementById('hetznerNotConnected').style.display = 'block';
                document.getElementById('hetznerConnected').style.display = 'none';
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        function showHetznerConnected(servers) {
            document.getElementById('hetznerNotConnected').style.display = 'none';
            document.getElementById('hetznerConnected').style.display = 'flex';
            document.getElementById('hetznerServers').textContent = `${servers} servidor(es) activo(s)`;
        }
        
        async function checkHetznerStatus() {
            try {
                const response = await fetch('/api/settings/hetzner');
                const data = await response.json();
                if (data.connected) {
                    showHetznerConnected(data.servers || 0);
                }
            } catch (error) {
                console.error('Error checking Hetzner status:', error);
            }
        }
        
        // ============================================
        // Hetzner Server Management Functions
        // ============================================
        
        async function checkHetznerServerInfo() {
            try {
                const response = await fetch('/api/settings/hetzner/server');
                const data = await response.json();
                
                if (data.server) {
                    document.getElementById('hetznerServerInfo').style.display = 'block';
                    document.getElementById('serverIP').textContent = data.server.ip;
                    document.getElementById('serverStatus').textContent = data.server.status === 'running' ? '🟢 Online' : '🔴 Offline';
                    document.getElementById('sshPassword').textContent = data.server.ssh_password || '••••••••';
                    document.getElementById('sshCommand').textContent = `ssh root@${data.server.ip}`;
                    document.getElementById('serverURL').href = `http://${data.server.ip}`;
                }
            } catch (error) {
                console.error('Error checking server info:', error);
            }
        }
        
        function copySSHCommand() {
            const cmd = document.getElementById('sshCommand').textContent;
            navigator.clipboard.writeText(cmd);
            alert('✅ Comando SSH copiado al portapapeles');
        }
        
        async function viewServerLogs() {
            const container = document.getElementById('serverLogsContainer');
            const logsEl = document.getElementById('serverLogs');
            
            container.style.display = 'block';
            logsEl.textContent = '⏳ Cargando logs...';
            
            try {
                const response = await fetch('/api/settings/hetzner/logs');
                const data = await response.json();
                
                if (data.logs) {
                    logsEl.textContent = data.logs;
                    // Scroll al final
                    logsEl.scrollTop = logsEl.scrollHeight;
                } else {
                    logsEl.textContent = '❌ Error: ' + (data.error || 'No se pudieron obtener los logs');
                }
            } catch (error) {
                logsEl.textContent = '❌ Error de conexión: ' + error.message;
            }
        }
        
        async function refreshServerLogs() {
            await viewServerLogs();
        }
        
        async function restartServer() {
            if (!confirm('¿Estás seguro de reiniciar el servidor? La app estará offline por unos segundos.')) {
                return;
            }
            
            try {
                const response = await fetch('/api/settings/hetzner/restart', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ Servidor reiniciando... Espera unos segundos y recarga la página.');
                    document.getElementById('serverStatus').textContent = '🟡 Reiniciando...';
                } else {
                    alert('❌ Error: ' + (data.error || 'No se pudo reiniciar'));
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }
        
        // =============================================
        // TURSO DATABASE
        // =============================================
        
        async function checkTursoStatus() {
            try {
                const response = await fetch('/api/settings/turso');
                const data = await response.json();
                
                if (data.connected) {
                    document.getElementById('tursoNotConnected').style.display = 'none';
                    document.getElementById('tursoConnected').style.display = 'flex';
                    document.getElementById('tursoUrl').textContent = data.url || '';
                } else {
                    document.getElementById('tursoNotConnected').style.display = 'block';
                    document.getElementById('tursoConnected').style.display = 'none';
                    if (data.url) {
                        document.getElementById('turso_url').value = data.url;
                    }
                }
            } catch (error) {
                console.error('Error checking Turso status:', error);
            }
        }
        
        async function saveTursoConfig() {
            const url = document.getElementById('turso_url').value.trim();
            const token = document.getElementById('turso_token').value.trim();
            
            if (!url || !token) {
                alert('Por favor ingresa URL y Token');
                return;
            }
            
            try {
                const response = await fetch('/api/settings/turso', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, token })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ Turso configurado correctamente');
                    checkTursoStatus();
                } else {
                    alert('❌ Error: ' + (data.error || 'No se pudo conectar'));
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }
        
        async function disconnectTurso() {
            if (!confirm('¿Desconectar Turso y volver a SQLite local?')) return;
            
            try {
                const response = await fetch('/api/settings/turso', {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ Turso desconectado');
                    checkTursoStatus();
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }
        
        // Llamar checks al cargar
        document.addEventListener('DOMContentLoaded', () => {
            checkTavilyStatus();
            checkHetznerStatus();
            checkHetznerServerInfo();
            checkTursoStatus();
        });
