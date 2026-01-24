/**
 * Advanced Features JS - TOP-tier AI Agent capabilities
 * Features: MCP Protocol, Diff Preview, Codemaps, Undo/Checkpoints, Voice Input
 */

// ============================================
// 1. MCP PROTOCOL UI
// ============================================

async function showMCPPanel() {
    try {
        const response = await fetch('/api/features/mcp/servers');
        const data = await response.json();
        
        let html = `
            <div class="mcp-panel">
                <h3>🔌 MCP Protocol</h3>
                <p class="mcp-description">Conecta herramientas externas al agente</p>
                <div class="mcp-servers">
        `;
        
        for (const server of data.servers || []) {
            const isConnected = server.status === 'connected';
            const btnClass = isConnected ? 'connected' : '';
            const btnText = isConnected ? 'Desconectar' : 'Conectar';
            const btnAction = isConnected ? 'disconnectMCPServer' : 'connectMCPServer';
            
            html += `
                <div class="mcp-server-item ${isConnected ? 'connected' : ''}">
                    <div class="mcp-server-info">
                        <strong>${server.name}</strong>
                        <span>${server.description}</span>
                        ${server.requires_env ? `<small class="env-warning">Requiere: ${server.env_vars.join(', ')}</small>` : ''}
                    </div>
                    <button class="mcp-connect-btn ${btnClass}" onclick="${btnAction}('${server.id}')">
                        ${btnText}
                    </button>
                </div>
            `;
        }
        
        html += `
                </div>
                <p class="mcp-note">💡 MCP extiende las capacidades del agente con herramientas externas. <a href="https://modelcontextprotocol.io" target="_blank">Más info</a></p>
            </div>
        `;
        
        showModal('MCP Protocol', html);
    } catch (e) {
        showToast('Error cargando MCP servers', 'error');
    }
}

async function connectMCPServer(serverId) {
    try {
        showToast('Conectando a ' + serverId + '...', 'info');
        
        const formData = new FormData();
        formData.append('server_id', serverId);
        
        const response = await fetch('/api/features/mcp/connect', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`✅ Conectado a ${serverId}. ${data.tools || 0} herramientas disponibles.`, 'success');
            showMCPPanel(); // Refrescar panel
        } else {
            showToast('❌ Error: ' + (data.detail || data.error), 'error');
        }
    } catch (e) {
        showToast('Error conectando: ' + e.message, 'error');
    }
}

async function disconnectMCPServer(serverId) {
    try {
        const formData = new FormData();
        formData.append('server_id', serverId);
        
        const response = await fetch('/api/features/mcp/disconnect', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Desconectado de ' + serverId, 'success');
            showMCPPanel(); // Refrescar panel
        } else {
            showToast('Error: ' + (data.detail || data.error), 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}


// ============================================
// 2. DIFF PREVIEW UI
// ============================================

async function showDiffPreview(original, modified, filename) {
    try {
        const formData = new FormData();
        formData.append('original', original);
        formData.append('modified', modified);
        formData.append('filename', filename || 'file');
        
        const response = await fetch('/api/features/diff/generate', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        const html = `
            <div class="diff-preview">
                <div class="diff-stats">
                    <span class="diff-additions">+${data.additions} adiciones</span>
                    <span class="diff-deletions">-${data.deletions} eliminaciones</span>
                </div>
                <pre class="diff-content">${escapeHtml(data.diff)}</pre>
                <div class="diff-actions">
                    <button class="diff-btn apply" onclick="applyDiff()">✅ Aplicar cambios</button>
                    <button class="diff-btn reject" onclick="closeModal()">❌ Rechazar</button>
                </div>
            </div>
        `;
        
        showModal(`Cambios en ${filename}`, html);
    } catch (e) {
        showToast('Error generando diff', 'error');
    }
}


// ============================================
// 3. CODEMAPS UI
// ============================================

async function showCodemaps() {
    const workspace = window.currentWorkspace || '/workspace/project/test03';
    
    const html = `
        <div class="codemaps-panel">
            <h3>🗺️ Codemaps</h3>
            <div class="codemap-options">
                <button class="codemap-btn" onclick="generateCodemap('structure')">
                    📁 Estructura de archivos
                </button>
                <button class="codemap-btn" onclick="generateCodemap('classes')">
                    📦 Diagrama de clases
                </button>
                <button class="codemap-btn" onclick="generateCodemap('flow')">
                    🔀 Diagrama de flujo
                </button>
            </div>
            <div id="codemapResult" class="codemap-result"></div>
        </div>
    `;
    
    showModal('Codemaps', html);
}

async function generateCodemap(type) {
    const resultDiv = document.getElementById('codemapResult');
    resultDiv.innerHTML = '<div class="loading">Generando diagrama...</div>';
    
    try {
        let formData = new FormData();
        let endpoint = '';
        
        if (type === 'structure') {
            formData.append('directory', window.currentWorkspace || '/workspace/project/test03');
            formData.append('max_depth', '3');
            endpoint = '/api/features/codemaps/structure';
        } else if (type === 'classes') {
            // Para demo, usar código de ejemplo
            formData.append('code', 'class Example:\\n    pass\\n\\nclass Child(Example):\\n    pass');
            endpoint = '/api/features/codemaps/classes';
        } else {
            formData.append('description', 'Flujo de ejemplo');
            endpoint = '/api/features/codemaps/flow';
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        // Renderizar Mermaid
        resultDiv.innerHTML = `
            <div class="mermaid">${data.mermaid}</div>
            <pre class="mermaid-source">${escapeHtml(data.mermaid)}</pre>
        `;
        
        // Re-renderizar Mermaid si está disponible
        if (window.mermaid) {
            mermaid.init(undefined, resultDiv.querySelector('.mermaid'));
        }
    } catch (e) {
        resultDiv.innerHTML = `<div class="error">Error: ${e.message}</div>`;
    }
}


// ============================================
// 4. CHECKPOINTS UI
// ============================================

let checkpointWorkspace = '';

async function showCheckpoints() {
    checkpointWorkspace = window.currentWorkspace || '/workspace/project/test03';
    
    const html = `
        <div class="checkpoints-panel">
            <h3>↩️ Checkpoints</h3>
            <p>Guarda el estado actual para poder volver atrás</p>
            
            <div class="checkpoint-create">
                <input type="text" id="checkpointDesc" placeholder="Descripción (opcional)">
                <button class="checkpoint-btn create" onclick="createCheckpoint()">
                    📌 Crear Checkpoint
                </button>
            </div>
            
            <h4>Checkpoints guardados:</h4>
            <div id="checkpointsList" class="checkpoints-list">
                <div class="loading">Cargando...</div>
            </div>
        </div>
    `;
    
    showModal('Checkpoints', html);
    loadCheckpoints();
}

async function loadCheckpoints() {
    try {
        const response = await fetch(`/api/features/checkpoints/list?workspace=${encodeURIComponent(checkpointWorkspace)}`);
        const data = await response.json();
        
        const listDiv = document.getElementById('checkpointsList');
        
        if (!data.checkpoints || data.checkpoints.length === 0) {
            listDiv.innerHTML = '<p class="no-checkpoints">No hay checkpoints guardados</p>';
            return;
        }
        
        let html = '';
        for (const cp of data.checkpoints) {
            html += `
                <div class="checkpoint-item">
                    <div class="checkpoint-info">
                        <span class="checkpoint-ref">${cp.ref}</span>
                        <span class="checkpoint-desc">${cp.description}</span>
                    </div>
                    <button class="checkpoint-restore-btn" onclick="restoreCheckpoint('${cp.ref}')">
                        ↩️ Restaurar
                    </button>
                </div>
            `;
        }
        
        listDiv.innerHTML = html;
    } catch (e) {
        document.getElementById('checkpointsList').innerHTML = `<div class="error">Error: ${e.message}</div>`;
    }
}

async function createCheckpoint() {
    const desc = document.getElementById('checkpointDesc').value;
    
    try {
        const formData = new FormData();
        formData.append('workspace', checkpointWorkspace);
        formData.append('description', desc);
        
        const response = await fetch('/api/features/checkpoints/create', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.success) {
            showToast('Checkpoint creado: ' + data.id, 'success');
            document.getElementById('checkpointDesc').value = '';
            loadCheckpoints();
        } else {
            showToast('Error: ' + (data.error || 'No se pudo crear'), 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function restoreCheckpoint(ref) {
    if (!confirm('¿Restaurar este checkpoint? Los cambios actuales se perderán.')) return;
    
    try {
        const formData = new FormData();
        formData.append('workspace', checkpointWorkspace);
        formData.append('ref', ref);
        
        const response = await fetch('/api/features/checkpoints/restore', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.success) {
            showToast('Checkpoint restaurado', 'success');
            closeModal();
        } else {
            showToast('Error: ' + (data.error || data.message), 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}


// ============================================
// 5. VOICE INPUT UI
// ============================================

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

function initVoiceInput() {
    // Agregar botón de micrófono si no existe
    const inputContainer = document.querySelector('.chat-input-row');
    if (inputContainer && !document.getElementById('voiceBtn')) {
        const voiceBtn = document.createElement('button');
        voiceBtn.type = 'button';
        voiceBtn.id = 'voiceBtn';
        voiceBtn.className = 'voice-btn';
        voiceBtn.innerHTML = '🎤';
        voiceBtn.title = 'Grabar voz (mantener presionado)';
        voiceBtn.onmousedown = startRecording;
        voiceBtn.onmouseup = stopRecording;
        voiceBtn.onmouseleave = stopRecording;
        voiceBtn.ontouchstart = startRecording;
        voiceBtn.ontouchend = stopRecording;
        
        // Insertar antes del botón de adjuntar
        const attachBtn = inputContainer.querySelector('.attach-btn');
        if (attachBtn) {
            attachBtn.parentNode.insertBefore(voiceBtn, attachBtn);
        }
    }
}

async function startRecording(e) {
    e.preventDefault();
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await transcribeAudio(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        isRecording = true;
        document.getElementById('voiceBtn').classList.add('recording');
        document.getElementById('voiceBtn').innerHTML = '🔴';
    } catch (e) {
        showToast('Error accediendo al micrófono: ' + e.message, 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        document.getElementById('voiceBtn').classList.remove('recording');
        document.getElementById('voiceBtn').innerHTML = '🎤';
    }
}

async function transcribeAudio(audioBlob) {
    try {
        showToast('Transcribiendo...', 'info');
        
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        const response = await fetch('/api/features/voice/transcribe', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.success && data.text) {
            // Insertar texto en el input
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                const currentText = messageInput.innerText || messageInput.textContent || '';
                messageInput.innerText = currentText + (currentText ? ' ' : '') + data.text;
                messageInput.focus();
            }
            showToast('Transcripción completada', 'success');
        } else {
            showToast('Error en transcripción: ' + (data.error || 'Sin resultado'), 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}


// ============================================
// TOOLS MENU
// ============================================

function showToolsMenu() {
    const menu = document.getElementById('toolsMenu');
    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        return;
    }
    
    // Crear menú si no existe
    const toolsBtn = document.querySelector('.tools-btn');
    if (!toolsBtn) return;
    
    const menuHtml = `
        <div id="toolsMenu" class="tools-menu" style="position: absolute; bottom: 45px; max-height: 400px; overflow-y: auto; left: 0; background: #1e1e1e; border: 1px solid #444; border-radius: 8px; padding: 8px; margin-bottom: 8px; min-width: 200px; z-index: 1000; box-shadow: 0 -4px 12px rgba(0,0,0,0.3);">
            <button onclick="showMCPPanel()">🔌 MCP Protocol</button>
            <button onclick="showEmbeddingsPanel()">🧠 Code Embeddings</button>
            <button onclick="showCodemaps()">🗺️ Codemaps</button>
            <button onclick="showCheckpoints()">↩️ Checkpoints</button>
            <button onclick="showVoiceSettings()">🎤 Voice Input</button>
            <button onclick="showBackgroundPanel()">🔄 Background Agents</button>
            <button onclick="openSandboxModal()">🖥️ Code Sandbox</button>
            <hr>
            <button onclick="showFeaturesStatus()">ℹ️ Estado de Features</button>
        </div>
    `;
    
    toolsBtn.insertAdjacentHTML('afterend', menuHtml);
    document.getElementById('toolsMenu').style.display = 'block';
    
    // Cerrar al hacer clic fuera
    document.addEventListener('click', function closeMenu(e) {
        if (!e.target.closest('.tools-btn') && !e.target.closest('.tools-menu')) {
            const menu = document.getElementById('toolsMenu');
            if (menu) menu.style.display = 'none';
        }
    });
}

// ============================================
// CODEBASE EMBEDDINGS UI
// ============================================

async function showEmbeddingsPanel() {
    const workspace = window.currentWorkspace || '/workspace/project/test03';
    
    try {
        // Obtener estado actual
        const response = await fetch(`/api/features/embeddings/status?workspace=${encodeURIComponent(workspace)}`);
        const status = await response.json();
        
        let html = `
            <div class="embeddings-panel">
                <h3>🧠 Codebase Embeddings</h3>
                <p class="embeddings-description">Indexa tu código para búsqueda semántica inteligente</p>
                
                <div class="embeddings-status">
                    <div class="status-item ${status.available !== false ? 'ok' : 'error'}">
                        <span>ChromaDB:</span>
                        <span>${status.missing?.chromadb === false ? '✅' : '❌'}</span>
                    </div>
                    <div class="status-item ${status.available !== false ? 'ok' : 'error'}">
                        <span>Sentence Transformers:</span>
                        <span>${status.missing?.sentence_transformers === false ? '✅' : '❌'}</span>
                    </div>
                    <div class="status-item">
                        <span>Chunks indexados:</span>
                        <span>${status.total_chunks || 0}</span>
                    </div>
                </div>
                
                <div class="embeddings-actions">
                    <button class="embeddings-btn index" onclick="indexCodebase()">
                        📚 Indexar Codebase
                    </button>
                    <button class="embeddings-btn reindex" onclick="indexCodebase(true)">
                        🔄 Re-indexar Todo
                    </button>
                </div>
                
                <div class="embeddings-search">
                    <h4>Buscar código</h4>
                    <input type="text" id="embeddingsQuery" placeholder="Ej: función que maneja autenticación">
                    <button class="embeddings-btn search" onclick="searchCodebase()">
                        🔍 Buscar
                    </button>
                </div>
                
                <div id="embeddingsResults" class="embeddings-results"></div>
            </div>
        `;
        
        showModal('Codebase Embeddings', html);
    } catch (e) {
        showToast('Error cargando embeddings: ' + e.message, 'error');
    }
}

async function indexCodebase(force = false) {
    const workspace = window.currentWorkspace || '/workspace/project/test03';
    
    try {
        showToast('Indexando codebase... esto puede tomar unos segundos', 'info');
        
        const formData = new FormData();
        formData.append('workspace', workspace);
        formData.append('force', force.toString());
        
        const response = await fetch('/api/features/embeddings/index', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success || data.indexed_files !== undefined) {
            showToast(`✅ Indexados ${data.indexed_files} archivos (${data.indexed_chunks} chunks)`, 'success');
            showEmbeddingsPanel(); // Refrescar
        } else {
            showToast('❌ Error: ' + (data.detail || data.error), 'error');
        }
    } catch (e) {
        showToast('Error indexando: ' + e.message, 'error');
    }
}

async function searchCodebase() {
    const workspace = window.currentWorkspace || '/workspace/project/test03';
    const query = document.getElementById('embeddingsQuery').value;
    
    if (!query.trim()) {
        showToast('Ingresa una búsqueda', 'error');
        return;
    }
    
    const resultsDiv = document.getElementById('embeddingsResults');
    resultsDiv.innerHTML = '<div class="loading">Buscando...</div>';
    
    try {
        const formData = new FormData();
        formData.append('workspace', workspace);
        formData.append('query', query);
        formData.append('n_results', '5');
        
        const response = await fetch('/api/features/embeddings/search', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success && data.results) {
            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<p class="no-results">No se encontraron resultados. ¿Ya indexaste el codebase?</p>';
                return;
            }
            
            let html = '';
            for (const result of data.results) {
                html += `
                    <div class="search-result">
                        <div class="result-header">
                            <span class="result-file">${result.filepath}</span>
                            <span class="result-lines">Líneas ${result.start_line}-${result.end_line}</span>
                            <span class="result-relevance">${Math.round(result.relevance * 100)}%</span>
                        </div>
                        <pre class="result-code">${escapeHtml(result.code.substring(0, 300))}${result.code.length > 300 ? '...' : ''}</pre>
                    </div>
                `;
            }
            
            resultsDiv.innerHTML = html;
        } else {
            resultsDiv.innerHTML = `<div class="error">Error: ${data.detail || data.error || 'Sin resultados'}</div>`;
        }
    } catch (e) {
        resultsDiv.innerHTML = `<div class="error">Error: ${e.message}</div>`;
    }
}

async function showFeaturesStatus() {
    try {
        const response = await fetch('/api/features/status');
        const data = await response.json();
        
        let html = '<div class="features-status">';
        
        const features = [
            { key: 'mcp', name: 'MCP Protocol', icon: '🔌' },
            { key: 'diff_preview', name: 'Diff Preview', icon: '📊' },
            { key: 'codemaps', name: 'Codemaps', icon: '🗺️' },
            { key: 'checkpoints', name: 'Checkpoints', icon: '↩️' },
            { key: 'voice_input', name: 'Voice Input', icon: '🎤' },
            { key: 'image_vision', name: 'Image Vision', icon: '🖼️' }
        ];
        
        for (const f of features) {
            const status = data[f.key];
            const enabled = status?.enabled !== false;
            html += `
                <div class="feature-status-item ${enabled ? 'enabled' : 'disabled'}">
                    <span class="feature-icon">${f.icon}</span>
                    <span class="feature-name">${f.name}</span>
                    <span class="feature-badge">${enabled ? '✅' : '❌'}</span>
                </div>
            `;
        }
        
        html += '</div>';
        
        showModal('Estado de Features', html);
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}


// ============================================
// MODAL & HELPERS
// ============================================

function showModal(title, content) {
    // Remover modal existente
    const existing = document.getElementById('featureModal');
    if (existing) existing.remove();
    
    const modal = document.createElement('div');
    modal.id = 'featureModal';
    modal.className = 'feature-modal';
    modal.innerHTML = `
        <div class="feature-modal-content">
            <div class="feature-modal-header">
                <h2>${title}</h2>
                <button class="modal-close" onclick="closeModal()">×</button>
            </div>
            <div class="feature-modal-body">
                ${content}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.getElementById('featureModal');
    if (modal) modal.remove();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Override toggleTools si existe
if (typeof window.toggleTools === 'function') {
    window._originalToggleTools = window.toggleTools;
}
window.toggleTools = showToolsMenu;

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', function() {
    // Cargar Mermaid si no existe
    if (!window.mermaid) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js';
        script.onload = () => mermaid.initialize({ startOnLoad: true, theme: 'dark' });
        document.head.appendChild(script);
    }
});
