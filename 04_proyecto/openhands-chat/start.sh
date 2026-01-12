#!/bin/bash
# ==============================================
# SCRIPT DE INICIO - OpenHands Chat
# Este script instala todas las dependencias
# y levanta la aplicación automáticamente
# ==============================================

set -e  # Salir si hay error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  🚀 INICIANDO OPENHANDS CHAT"
echo "=============================================="

# === 1. INSTALAR DEPENDENCIAS PIP ===
echo ""
echo "📦 Instalando dependencias de Python..."
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt

# === 2. INSTALAR CODE-SERVER (VS Code en navegador) ===
if ! command -v code-server &> /dev/null; then
    echo ""
    echo "💻 Instalando code-server (VS Code)..."
    curl -fsSL https://code-server.dev/install.sh | sh -s -- --method=standalone --prefix=$HOME/.local 2>/dev/null
    export PATH="$HOME/.local/bin:$PATH"
fi

# === 3. MATAR PROCESOS ANTERIORES ===
echo ""
echo "🧹 Limpiando procesos anteriores..."
pkill -f "python app.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -9 -f "code-server" 2>/dev/null || true
sleep 2

# === 4. INICIAR LA APLICACIÓN ===
echo ""
echo "🌐 Iniciando servidor..."
export PORT=12000
export PATH="$HOME/.local/bin:$PATH"

# Iniciar en background
python app.py > server.log 2>&1 &
APP_PID=$!

# Esperar a que inicie
sleep 5

# Verificar que está corriendo
if curl -s http://localhost:12000/health > /dev/null 2>&1; then
    echo ""
    echo "=============================================="
    echo "  ✅ OPENHANDS CHAT INICIADO CORRECTAMENTE"
    echo "=============================================="
    echo ""
    echo "  🌐 URL: https://work-1-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev"
    echo "  📁 Logs: $SCRIPT_DIR/server.log"
    echo "  🔧 PID: $APP_PID"
    echo ""
else
    echo ""
    echo "❌ ERROR: El servidor no inició correctamente"
    echo "Revisa los logs: cat $SCRIPT_DIR/server.log"
    cat server.log | tail -20
    exit 1
fi
