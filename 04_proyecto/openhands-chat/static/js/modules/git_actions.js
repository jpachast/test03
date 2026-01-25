/**
 * Git Actions Module - GitHub integration
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    // === ACCIONES GIT ===
    let currentGitInfo = { owner: '', repo: '', branch: 'main' };
    
    // SVG icons para los botones Git
    const gitIcons = {
        pull: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M7.47 10.78a.75.75 0 001.06 0l3.75-3.75a.75.75 0 00-1.06-1.06L8.75 8.44V1.75a.75.75 0 00-1.5 0v6.69L4.78 5.97a.75.75 0 00-1.06 1.06l3.75 3.75zM3.75 13a.75.75 0 000 1.5h8.5a.75.75 0 000-1.5h-8.5z"/></svg>',
        push: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M8.53 1.22a.75.75 0 00-1.06 0L3.72 4.97a.75.75 0 001.06 1.06l2.47-2.47v6.69a.75.75 0 001.5 0V3.56l2.47 2.47a.75.75 0 101.06-1.06L8.53 1.22zM3.75 13a.75.75 0 000 1.5h8.5a.75.75 0 000-1.5h-8.5z"/></svg>',
        pr: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/></svg>',
        loading: '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" class="spin"><path d="M8 0a8 8 0 100 16A8 8 0 008 0zm0 1.5a6.5 6.5 0 110 13 6.5 6.5 0 010-13z" opacity="0.3"/><path d="M8 0a8 8 0 018 8h-1.5A6.5 6.5 0 008 1.5V0z"/></svg>'
    };
    
    function updateGitBar(owner, repo, branch) {
        currentGitInfo = { owner, repo, branch: branch || 'main' };
        const repoFullName = `${owner}/${repo}`;
        const branchName = branch || 'main';
        
        // Actualizar texto
        const repoNameEl = document.getElementById('gitRepoName');
        const branchNameEl = document.getElementById('gitBranchName');
        if (repoNameEl) repoNameEl.textContent = repoFullName;
        if (branchNameEl) branchNameEl.textContent = branchName;
        
        // Actualizar URLs de los links
        const repoLink = document.getElementById('gitRepoLink');
        const branchLink = document.getElementById('gitBranchLink');
        
        if (repoLink) {
            repoLink.href = `https://github.com/${repoFullName}`;
        }
        if (branchLink) {
            branchLink.href = `https://github.com/${repoFullName}/tree/${branchName}`;
        }
    }
    
    // Git buttons - EXACTAMENTE como OpenHands
    function gitPull() {
        const pullPrompt = "Please pull the latest code from the repository.";
        if (window.setMessageInputValue) {
            window.setMessageInputValue(pullPrompt);
        }
        if (window.sendMessage) {
            window.sendMessage(new Event('submit'));
        }
    }
    
    function gitPush() {
        const pushPrompt = "Please push the changes to a remote branch on GitHub, but do NOT create a Pull Request. " +
            "Check your current branch name first - if it's main, master, deploy, or another common default branch name, " +
            "create a new branch with a descriptive name related to your changes. " +
            "Otherwise, use the exact SAME branch name as the one you are currently on.";
        if (window.setMessageInputValue) {
            window.setMessageInputValue(pushPrompt);
        }
        if (window.sendMessage) {
            window.sendMessage(new Event('submit'));
        }
    }
    
    function createPR() {
        const prPrompt = "Please push the changes to GitHub and open a Pull Request. " +
            "If you're on a default branch (e.g., main, master, deploy), create a new branch with a descriptive name " +
            "otherwise use the current branch. " +
            "If a Pull Request template exists in the repository, please follow it when creating the PR description.";
        if (window.setMessageInputValue) {
            window.setMessageInputValue(prPrompt);
        }
        if (window.sendMessage) {
            window.sendMessage(new Event('submit'));
        }
    }
    
    function getCurrentGitInfo() {
        return { ...currentGitInfo };
    }
    
    function getIcons() {
        return { ...gitIcons };
    }
    
    // Exponer funciones globalmente
    window.GitActionsModule = {
        updateBar: updateGitBar,
        pull: gitPull,
        push: gitPush,
        createPR: createPR,
        getInfo: getCurrentGitInfo,
        icons: gitIcons
    };
    
    // Alias para compatibilidad
    window.updateGitBar = updateGitBar;
    window.gitPull = gitPull;
    window.gitPush = gitPush;
    window.createPR = createPR;
    window.gitIcons = gitIcons;
    window.currentGitInfo = currentGitInfo;
    
})();
