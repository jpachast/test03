/**
 * UI State Module - Agent state and task tracker
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    let currentAgentState = 'idle';
    let currentTasks = [];
    
    function setTaskStatus(status, text) {
        const taskStatus = document.getElementById('taskStatus');
        const statusText = document.getElementById('statusText');
        
        if (taskStatus) taskStatus.className = 'task-status ' + status;
        if (statusText) statusText.textContent = text;
        
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
    
    function updateTaskTrackerUI(tasks) {
        if (!tasks || tasks.length === 0) return;
        
        currentTasks = tasks;
        
        let taskContainer = document.getElementById('taskTrackerContainer');
        if (!taskContainer) {
            taskContainer = document.createElement('div');
            taskContainer.id = 'taskTrackerContainer';
            taskContainer.className = 'task-tracker-container';
            
            const rightPanel = document.querySelector('.right-panel');
            if (rightPanel) {
                rightPanel.insertBefore(taskContainer, rightPanel.firstChild);
            }
        }
        
        const taskHTML = tasks.map((task, idx) => {
            const status = task.status || 'todo';
            const title = task.title || `Tarea ${idx + 1}`;
            const notes = task.notes || '';
            
            let statusIcon = '○';
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
    
    function setAgentState(state) {
        currentAgentState = state;
        window.currentAgentState = state;
        
        const iconClock = document.getElementById('iconClock');
        const iconPause = document.getElementById('iconPause');
        const iconPlay = document.getElementById('iconPlay');
        const iconLoading = document.getElementById('iconLoading');
        const btn = document.getElementById('agentControlBtn');
        
        if (!btn) return;
        
        if (iconClock) iconClock.style.display = 'none';
        if (iconPause) iconPause.style.display = 'none';
        if (iconPlay) iconPlay.style.display = 'none';
        if (iconLoading) iconLoading.style.display = 'none';
        
        btn.classList.remove('clickable');
        btn.title = 'Estado del agente';
        
        switch(state) {
            case 'running':
                if (iconPause) iconPause.style.display = 'block';
                btn.classList.add('clickable');
                btn.title = 'Pausar agente';
                break;
            case 'paused':
            case 'stopped':
                if (iconPlay) iconPlay.style.display = 'block';
                btn.classList.add('clickable');
                btn.title = 'Reanudar agente';
                break;
            case 'loading':
                if (iconLoading) iconLoading.style.display = 'flex';
                break;
            case 'error':
                if (iconClock) iconClock.style.display = 'block';
                break;
            case 'idle':
            default:
                if (iconClock) iconClock.style.display = 'block';
                break;
        }
    }
    
    async function pauseAgent() {
        const currentConversationId = window.currentConversationId;
        if (!currentConversationId) return;
        
        setAgentState('loading');
        
        try {
            const response = await fetch(`/api/conversations/${currentConversationId}/pause`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                setAgentState('paused');
                const statusText = document.getElementById('statusText');
                if (statusText) statusText.textContent = 'Agente pausado.';
            } else {
                setAgentState('running');
            }
        } catch (e) {
            console.error('Error pausando agente:', e);
            setAgentState('running');
        }
    }
    
    async function resumeAgent() {
        const currentConversationId = window.currentConversationId;
        if (!currentConversationId) return;
        
        setAgentState('loading');
        
        try {
            const response = await fetch(`/api/conversations/${currentConversationId}/resume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                setAgentState('running');
                const statusText = document.getElementById('statusText');
                if (statusText) statusText.textContent = 'Agente ejecutándose...';
            } else {
                setAgentState('paused');
            }
        } catch (e) {
            console.error('Error reanudando agente:', e);
            setAgentState('paused');
        }
    }
    
    function toggleAgentState() {
        if (currentAgentState === 'running') {
            pauseAgent();
        } else if (currentAgentState === 'paused' || currentAgentState === 'stopped') {
            resumeAgent();
        }
    }
    
    function getAgentState() {
        return currentAgentState;
    }
    
    function getTasks() {
        return [...currentTasks];
    }
    
    // Exponer globalmente
    window.UIStateModule = {
        setTaskStatus: setTaskStatus,
        updateTasks: updateTaskTrackerUI,
        hideTasks: hideTaskTracker,
        setAgentState: setAgentState,
        pauseAgent: pauseAgent,
        resumeAgent: resumeAgent,
        toggleAgent: toggleAgentState,
        getAgentState: getAgentState,
        getTasks: getTasks
    };
    
    window.setTaskStatus = setTaskStatus;
    window.updateTaskTrackerUI = updateTaskTrackerUI;
    window.hideTaskTracker = hideTaskTracker;
    window.setAgentState = setAgentState;
    window.pauseAgent = pauseAgent;
    window.resumeAgent = resumeAgent;
    window.toggleAgentState = toggleAgentState;
    window.currentAgentState = currentAgentState;
    
})();
