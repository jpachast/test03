        function togglePassword() {
            const input = document.getElementById('api_key');
            input.type = input.type === 'password' ? 'text' : 'password';
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
