/**
 * GitHub Module - Repository management
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    let selectedRepo = null;
    let repos = [];
    
    async function loadGitHubRepos() {
        const repoSelect = document.getElementById('repoSelect');
        if (!repoSelect) return;
        
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
        const repoSelect = document.getElementById('repoSelect');
        const branchSelect = document.getElementById('branchSelect');
        const launchBtn = document.getElementById('launchBtn');
        
        if (!repoSelect || !branchSelect || !launchBtn) return;
        
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
        const branchSelect = document.getElementById('branchSelect');
        const launchBtn = document.getElementById('launchBtn');
        const chatMessages = document.getElementById('chatMessages');
        
        if (!selectedRepo || !branchSelect || !branchSelect.value) return;
        
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
                window.currentProject = data.project_name;
                window.currentConversationId = data.conversation_id;
                const convIdInput = document.getElementById('currentConversationId');
                if (convIdInput) convIdInput.value = data.conversation_id;
                
                if (window.showChat) {
                    window.showChat(data.project_name, `${selectedRepo.owner}/${selectedRepo.name}`, branchSelect.value);
                }
                if (chatMessages) {
                    chatMessages.innerHTML = '<div class="message system">👋 ¡Hola! Repositorio clonado correctamente. ¿Qué quieres hacer?</div>';
                }
                
                // PRE-INICIAR servidores
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
                
                if (window.showCodeTabs) window.showCodeTabs(selectedRepo.name);
                if (window.updateGitBar) window.updateGitBar(selectedRepo.owner, selectedRepo.name, branchSelect.value);
                window.codeServerLoaded = false;
                window.browserLoaded = false;
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
    
    function getSelectedRepo() {
        return selectedRepo ? { ...selectedRepo } : null;
    }
    
    function getRepos() {
        return [...repos];
    }
    
    // Exponer globalmente
    window.GitHubModule = {
        loadRepos: loadGitHubRepos,
        onSelect: onRepoSelect,
        launch: launchRepo,
        getSelected: getSelectedRepo,
        getRepos: getRepos
    };
    
    window.loadGitHubRepos = loadGitHubRepos;
    window.onRepoSelect = onRepoSelect;
    window.launchRepo = launchRepo;
    window.selectedRepo = selectedRepo;
    window.repos = repos;
    
})();
