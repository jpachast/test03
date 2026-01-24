// ============================================
// BACKGROUND AGENTS UI
// ============================================

// Estado global
let backgroundState = {
    tasks: [],
    polling: null,
    conversationId: null
};

// Inicializar Background Agents
function initBackgroundAgents(conversationId) {
    // Auto-detectar conversationId de la URL si no se proporciona
    if (!conversationId) {
        const match = window.location.pathname.match(/\/chat\/(\d+)/);
        if (match) {
            conversationId = parseInt(match[1]);
        }
    }
    backgroundState.conversationId = conversationId;
    
    // Empezar polling de notificaciones
    startNotificationPolling();
    
    // Cargar tareas activas
    loadActiveTasks();
}

// Polling de notificaciones
function startNotificationPolling() {
    if (backgroundState.polling) {
        clearInterval(backgroundState.polling);
    }
    
    backgroundState.polling = setInterval(async () => {
        await checkNotifications();
        await updateTasksUI();
    }, 5000); // Cada 5 segundos
}

function stopNotificationPolling() {
    if (backgroundState.polling) {
        clearInterval(backgroundState.polling);
        backgroundState.polling = null;
    }
}

// Verificar notificaciones
async function checkNotifications() {
    if (!backgroundState.conversationId) return;
    
    try {
        const response = await fetch(`/api/background/notifications/${backgroundState.conversationId}`);
        const data = await response.json();
        
        if (data.notifications && data.notifications.length > 0) {
            data.notifications.forEach(notif => {
                showBackgroundNotification(notif);
            });
        }
    } catch (e) {
        console.error('Error checking notifications:', e);
    }
}

// Mostrar notificación
function showBackgroundNotification(notif) {
    const isSuccess = notif.type === 'task_completed';
    const icon = isSuccess ? '✅' : '❌';
    const className = isSuccess ? 'success' : 'error';
    
    // Crear elemento de notificación
    const notifEl = document.createElement('div');
    notifEl.className = `background-notification ${className}`;
    notifEl.innerHTML = `
        <div class="notif-icon">${icon}</div>
        <div class="notif-content">
            <div class="notif-title">${notif.task_name}</div>
            <div class="notif-message">${notif.message}</div>
        </div>
        <button class="notif-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    // Agregar al DOM
    let container = document.getElementById('background-notifications');
    if (!container) {
        container = document.createElement('div');
        container.id = 'background-notifications';
        document.body.appendChild(container);
    }
    container.appendChild(notifEl);
    
    // Auto-remover después de 10 segundos
    setTimeout(() => notifEl.remove(), 10000);
    
    // También mostrar toast
    if (typeof showToast === 'function') {
        showToast(notif.message, isSuccess ? 'success' : 'error');
    }
}

// Cargar tareas activas
async function loadActiveTasks() {
    if (!backgroundState.conversationId) return;
    
    try {
        const response = await fetch(`/api/background/tasks/active?conversation_id=${backgroundState.conversationId}`);
        const data = await response.json();
        backgroundState.tasks = data.tasks || [];
        updateTasksUI();
    } catch (e) {
        console.error('Error loading tasks:', e);
    }
}

// Actualizar UI de tareas
function updateTasksUI() {
    const indicator = document.getElementById('background-tasks-indicator');
    const activeTasks = backgroundState.tasks.filter(t => 
        t.status === 'pending' || t.status === 'running'
    );
    
    if (activeTasks.length > 0) {
        if (!indicator) {
            createTasksIndicator();
        }
        updateTasksIndicator(activeTasks);
    } else {
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
}

// Crear indicador de tareas
function createTasksIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'background-tasks-indicator';
    indicator.className = 'background-tasks-indicator';
    indicator.innerHTML = `
        <div class="tasks-indicator-header" onclick="toggleTasksPanel()">
            <span class="tasks-spinner">⏳</span>
            <span class="tasks-count">0 tareas</span>
            <span class="tasks-toggle">▼</span>
        </div>
        <div class="tasks-panel" style="display:none;">
            <div class="tasks-list"></div>
        </div>
    `;
    document.body.appendChild(indicator);
}

// Actualizar indicador
function updateTasksIndicator(tasks) {
    const indicator = document.getElementById('background-tasks-indicator');
    if (!indicator) return;
    
    indicator.style.display = 'block';
    
    const countEl = indicator.querySelector('.tasks-count');
    const listEl = indicator.querySelector('.tasks-list');
    
    countEl.textContent = `${tasks.length} tarea${tasks.length > 1 ? 's' : ''} en progreso`;
    
    listEl.innerHTML = tasks.map(task => `
        <div class="task-item ${task.status}">
            <div class="task-header">
                <span class="task-name">${task.name}</span>
                <span class="task-status">${getStatusIcon(task.status)}</span>
            </div>
            <div class="task-progress">
                <div class="progress-bar" style="width: ${task.progress}%"></div>
            </div>
            <div class="task-info">
                <span class="task-duration">${task.duration || 'Iniciando...'}</span>
            </div>
        </div>
    `).join('');
}

function getStatusIcon(status) {
    const icons = {
        'pending': '⏳',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '🚫'
    };
    return icons[status] || '❓';
}

// Toggle panel de tareas
function toggleTasksPanel() {
    const panel = document.querySelector('.tasks-panel');
    const toggle = document.querySelector('.tasks-toggle');
    if (panel) {
        const isVisible = panel.style.display !== 'none';
        panel.style.display = isVisible ? 'none' : 'block';
        toggle.textContent = isVisible ? '▼' : '▲';
    }
}

// Crear tarea en background
async function createBackgroundTask(taskType, params = {}) {
    if (!backgroundState.conversationId) {
        showToast('No hay conversación activa', 'error');
        return null;
    }
    
    try {
        const response = await fetch('/api/background/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_type: taskType,
                conversation_id: backgroundState.conversationId,
                params: params
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`🚀 ${data.message}`, 'success');
            loadActiveTasks();
            return data.task;
        } else {
            showToast(`❌ Error: ${data.detail || 'No se pudo crear la tarea'}`, 'error');
            return null;
        }
    } catch (e) {
        showToast(`❌ Error: ${e.message}`, 'error');
        return null;
    }
}

// Mostrar panel de Background Agents
async function showBackgroundPanel() {
    try {
        const response = await fetch(`/api/background/tasks?conversation_id=${backgroundState.conversationId || ''}`);
        const data = await response.json();
        
        const tasks = data.tasks || [];
        
        let html = `
            <div class="background-panel">
                <h3>🔄 Tareas en Background</h3>
                <p class="panel-description">
                    Ejecuta tareas largas sin bloquear tu trabajo. Recibirás notificación cuando terminen.
                </p>
                
                <div class="quick-tasks">
                    <h4>Tareas Rápidas</h4>
                    <div class="quick-tasks-grid">
                        <button onclick="createBackgroundTask('analyze_codebase', {repo_path: '/workspace/project'})" class="quick-task-btn">
                            📊 Analizar Codebase
                        </button>
                        <button onclick="createBackgroundTask('git_pull', {repo_path: '/workspace/project'})" class="quick-task-btn">
                            ⬇️ Git Pull
                        </button>
                        <button onclick="createBackgroundTask('git_fetch', {repo_path: '/workspace/project'})" class="quick-task-btn">
                            🔄 Git Fetch
                        </button>
                        <button onclick="promptRunTests()" class="quick-task-btn">
                            🧪 Ejecutar Tests
                        </button>
                    </div>
                </div>
                
                <div class="tasks-history">
                    <h4>Historial de Tareas</h4>
                    ${tasks.length === 0 ? 
                        '<p class="no-tasks">No hay tareas recientes</p>' :
                        `<div class="tasks-history-list">
                            ${tasks.map(task => `
                                <div class="history-task ${task.status}">
                                    <div class="history-task-header">
                                        <span class="status-icon">${getStatusIcon(task.status)}</span>
                                        <span class="task-name">${task.name}</span>
                                        <span class="task-time">${task.duration || '-'}</span>
                                    </div>
                                    ${task.status === 'running' ? `
                                        <div class="task-progress">
                                            <div class="progress-bar" style="width: ${task.progress}%"></div>
                                        </div>
                                    ` : ''}
                                    ${task.error ? `<div class="task-error">${task.error}</div>` : ''}
                                </div>
                            `).join('')}
                        </div>`
                    }
                </div>
            </div>
        `;
        
        showModal('Background Agents', html);
    } catch (e) {
        showToast('Error cargando tareas: ' + e.message, 'error');
    }
}

// Prompt para ejecutar tests
function promptRunTests() {
    const command = prompt('Comando para ejecutar tests:', 'npm test');
    if (command) {
        createBackgroundTask('run_tests', {
            command: command,
            cwd: '/workspace/project'
        });
    }
}

// Estilos CSS para Background Agents
const backgroundStyles = `
<style>
/* Notificaciones */
#background-notifications {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.background-notification {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    background: #1e1e2e;
    border: 1px solid #313244;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    animation: slideIn 0.3s ease;
    max-width: 350px;
}

.background-notification.success {
    border-color: #a6e3a1;
}

.background-notification.error {
    border-color: #f38ba8;
}

.notif-icon {
    font-size: 24px;
}

.notif-content {
    flex: 1;
}

.notif-title {
    font-weight: 600;
    color: #cdd6f4;
}

.notif-message {
    font-size: 12px;
    color: #a6adc8;
}

.notif-close {
    background: none;
    border: none;
    color: #6c7086;
    font-size: 20px;
    cursor: pointer;
}

@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* Indicador de tareas */
.background-tasks-indicator {
    position: fixed;
    bottom: 80px;
    right: 20px;
    z-index: 1000;
    background: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 12px;
    min-width: 200px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.tasks-indicator-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    cursor: pointer;
    border-bottom: 1px solid #313244;
}

.tasks-spinner {
    animation: spin 2s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.tasks-count {
    flex: 1;
    color: #cdd6f4;
    font-weight: 500;
}

.tasks-panel {
    max-height: 300px;
    overflow-y: auto;
}

.tasks-list {
    padding: 8px;
}

.task-item {
    padding: 10px;
    border-radius: 8px;
    background: #181825;
    margin-bottom: 8px;
}

.task-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.task-name {
    color: #cdd6f4;
    font-weight: 500;
}

.task-progress {
    height: 4px;
    background: #313244;
    border-radius: 2px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #89b4fa, #b4befe);
    transition: width 0.3s;
}

.task-info {
    margin-top: 6px;
    font-size: 11px;
    color: #6c7086;
}

/* Panel de Background */
.background-panel h3 {
    margin: 0 0 8px 0;
    color: #89b4fa;
}

.panel-description {
    color: #6c7086;
    margin-bottom: 20px;
}

.quick-tasks h4 {
    color: #cdd6f4;
    margin: 0 0 12px 0;
}

.quick-tasks-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 24px;
}

.quick-task-btn {
    padding: 12px;
    background: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    color: #cdd6f4;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
}

.quick-task-btn:hover {
    background: #1e1e2e;
    border-color: #89b4fa;
}

.tasks-history h4 {
    color: #cdd6f4;
    margin: 0 0 12px 0;
}

.no-tasks {
    color: #6c7086;
    text-align: center;
    padding: 20px;
}

.tasks-history-list {
    max-height: 250px;
    overflow-y: auto;
}

.history-task {
    padding: 10px;
    background: #181825;
    border-radius: 8px;
    margin-bottom: 8px;
}

.history-task-header {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-icon {
    font-size: 16px;
}

.history-task .task-name {
    flex: 1;
}

.task-time {
    color: #6c7086;
    font-size: 12px;
}

.task-error {
    margin-top: 8px;
    padding: 8px;
    background: #f38ba820;
    border-radius: 4px;
    color: #f38ba8;
    font-size: 12px;
}
</style>
`;

// Inyectar estilos
document.head.insertAdjacentHTML('beforeend', backgroundStyles);


// Auto-inicializar si estamos en una página de chat
document.addEventListener('DOMContentLoaded', () => {
    const match = window.location.pathname.match(/\/chat\/(\d+)/);
    if (match) {
        initBackgroundAgents(parseInt(match[1]));
    }
});
