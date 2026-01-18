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
        
        // Llamar checkTavilyStatus al cargar
        document.addEventListener('DOMContentLoaded', checkTavilyStatus);
