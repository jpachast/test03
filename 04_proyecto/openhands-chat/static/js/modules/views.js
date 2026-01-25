/**
 * Views Module - Navigation and view switching
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    let currentView = 'chat';
    let browserLoaded = false;
    
    function showChat(projectName, repoFullName, branch) {
        const homeFullscreen = document.getElementById('homeFullscreen');
        const chatPage = document.getElementById('chatPage');
        const currentProjectInput = document.getElementById('currentProject');
        const repoNameEl = document.getElementById('repoName');
        const repoBranchEl = document.getElementById('repoBranch');
        const messageInput = document.getElementById('messageInput');
        
        if (homeFullscreen) homeFullscreen.style.display = 'none';
        if (chatPage) chatPage.style.display = 'flex';
        if (currentProjectInput) currentProjectInput.value = projectName;
        if (repoNameEl) repoNameEl.textContent = repoFullName || projectName || 'Nueva conversación';
        if (repoBranchEl) repoBranchEl.textContent = branch ? `🔀 ${branch}` : '';
        
        window.currentProject = projectName;
        
        // Actualizar barra de git
        const repoLink = document.getElementById('gitRepoLink');
        const branchLink = document.getElementById('gitBranchLink');
        const gitRepoName = document.getElementById('gitRepoName');
        const gitBranchName = document.getElementById('gitBranchName');
        
        if (repoFullName) {
            if (gitRepoName) gitRepoName.textContent = repoFullName;
            if (repoLink) {
                repoLink.href = `https://github.com/${repoFullName}`;
                repoLink.style.display = 'flex';
            }
        } else {
            if (gitRepoName) gitRepoName.textContent = projectName || '';
            if (repoLink) {
                repoLink.href = '#';
                repoLink.style.display = projectName ? 'flex' : 'none';
            }
        }
        
        if (branch && branch !== '') {
            if (gitBranchName) gitBranchName.textContent = branch;
            if (branchLink) {
                branchLink.href = repoFullName ? `https://github.com/${repoFullName}/tree/${branch}` : '#';
                branchLink.style.display = 'flex';
            }
        } else {
            if (branchLink) branchLink.style.display = 'none';
        }
        
        if (messageInput) messageInput.focus();
    }
    
    function goHome() {
        const homeFullscreen = document.getElementById('homeFullscreen');
        const chatPage = document.getElementById('chatPage');
        
        if (homeFullscreen) homeFullscreen.style.display = 'flex';
        if (chatPage) chatPage.style.display = 'none';
        
        window.currentConversationId = null;
        
        if (window.loadConversations) window.loadConversations();
        window.history.pushState({}, '', '/');
        switchView('chat');
        if (window.stopCodeServer) window.stopCodeServer();
    }
    
    function switchView(view) {
        currentView = view;
        window.currentView = view;
        
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
        if (tabChat) tabChat.classList.remove('active');
        if (tabCode) tabCode.classList.remove('active');
        if (tabApp) tabApp.classList.remove('active');
        if (tabBrowser) tabBrowser.classList.remove('active');
        if (tabTerminal) tabTerminal.classList.remove('active');
        
        // Ocultar todas las vistas
        if (appView) appView.style.display = 'none';
        if (codeViewRight) codeViewRight.style.display = 'none';
        if (browserView) browserView.style.display = 'none';
        if (terminalView) terminalView.style.display = 'none';
        
        if (view === 'chat') {
            if (appView) appView.style.display = 'block';
            if (tabChat) tabChat.classList.add('active');
        } else if (view === 'app') {
            if (appView) appView.style.display = 'block';
            if (tabApp) tabApp.classList.add('active');
            if (window.checkAppServer) window.checkAppServer();
        } else if (view === 'code') {
            if (codeViewRight) codeViewRight.style.display = 'block';
            if (tabCode) tabCode.classList.add('active');
            if (!window.codeServerLoaded && window.startCodeServer) {
                window.startCodeServer();
            }
        } else if (view === 'browser') {
            if (browserView) browserView.style.display = 'flex';
            if (tabBrowser) tabBrowser.classList.add('active');
            if (!browserLoaded && window.loadBrowserScreenshot) {
                window.loadBrowserScreenshot();
                browserLoaded = true;
            }
        } else if (view === 'terminal') {
            if (terminalView) {
                terminalView.style.display = 'flex';
                if (tabTerminal) tabTerminal.classList.add('active');
                setTimeout(() => {
                    if (window.initXterm) window.initXterm();
                }, 100);
            }
        }
    }
    
    function showCodeTabs(repoName) {
        const viewTabs = document.getElementById('viewTabs');
        const rightPanel = document.querySelector('.chat-right-panel');
        const leftPanel = document.querySelector('.chat-left-panel');
        
        if (viewTabs) viewTabs.style.display = 'flex';
        if (rightPanel) rightPanel.style.display = 'flex';
        if (leftPanel) leftPanel.style.flex = '';
    }
    
    function showHelp() {
        alert('🤖 OpenHands Chat\n\n1. Configura tu API key en Configuración\n2. Conecta tu cuenta de GitHub\n3. Selecciona un repositorio o empieza desde cero\n4. ¡Empieza a construir!');
    }
    
    function getCurrentView() {
        return currentView;
    }
    
    function setBrowserLoaded(value) {
        browserLoaded = value;
        window.browserLoaded = value;
    }
    
    // Exponer globalmente
    window.ViewsModule = {
        showChat: showChat,
        goHome: goHome,
        switchView: switchView,
        showCodeTabs: showCodeTabs,
        showHelp: showHelp,
        getCurrentView: getCurrentView,
        setBrowserLoaded: setBrowserLoaded
    };
    
    window.showChat = showChat;
    window.goHome = goHome;
    window.switchView = switchView;
    window.showCodeTabs = showCodeTabs;
    window.showHelp = showHelp;
    window.currentView = currentView;
    window.browserLoaded = browserLoaded;
    
})();
