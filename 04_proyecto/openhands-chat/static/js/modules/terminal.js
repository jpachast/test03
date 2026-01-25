/**
 * Terminal Module - xterm.js integration
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
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
    
    // Exponer funciones globalmente
    window.TerminalModule = {
        init: initXterm,
        addCommand: addTerminalCommand,
        addOutput: addTerminalOutput,
        scrollToBottom: scrollTerminalToBottom,
        clear: clearTerminal
    };
    
    // Alias para compatibilidad con código existente
    window.initXterm = initXterm;
    window.addTerminalCommand = addTerminalCommand;
    window.addTerminalOutput = addTerminalOutput;
    window.scrollTerminalToBottom = scrollTerminalToBottom;
    window.clearTerminal = clearTerminal;
    
})();
