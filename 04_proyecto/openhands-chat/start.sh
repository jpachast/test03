#!/bin/bash
# ==============================================
# SCRIPT DE INICIO - OpenHands Chat
# ==============================================
# USO: ./start.sh
# 
# Este script es solo un wrapper para python app.py
# La app se auto-configura completamente al iniciar.
# ==============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  🚀 INICIANDO OPENHANDS CHAT"
echo "=============================================="
echo ""

# Matar procesos anteriores si existen
pkill -f "python.*app.py" 2>/dev/null || true
sleep 1

# Iniciar la aplicación (auto-instala todo lo necesario)
echo "📦 Iniciando... (auto-instala dependencias si es necesario)"
echo ""

python app.py
