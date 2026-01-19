#!/bin/bash
# ==============================================
# SCRIPT DE INSTALACIÓN - OpenHands Chat
# ==============================================
# Instala TODAS las dependencias:
# - Sistema: chromium, nodejs, npm, ripgrep
# - Python: requirements.txt
# ==============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  📦 INSTALANDO OPENHANDS CHAT"
echo "=============================================="

# 1. Dependencias del sistema
echo ""
echo "🔧 Instalando dependencias del sistema..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq 2>/dev/null
    sudo apt-get install -y -qq chromium chromium-browser nodejs npm ripgrep git curl 2>/dev/null || \
    sudo apt-get install -y -qq chromium-browser nodejs npm ripgrep git curl 2>/dev/null
    sudo npm install -g npx 2>/dev/null
elif command -v dnf &> /dev/null; then
    sudo dnf install -y chromium nodejs npm ripgrep git curl 2>/dev/null
    sudo npm install -g npx 2>/dev/null
elif command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm chromium nodejs npm ripgrep git curl 2>/dev/null
    sudo npm install -g npx 2>/dev/null
fi

# 2. Dependencias Python
echo ""
echo "🐍 Instalando dependencias Python..."
pip install -q -r requirements.txt

# 3. Verificar instalación
echo ""
echo "✅ Verificando instalación..."
echo -n "  Chromium: "; (command -v chromium || command -v chromium-browser) &>/dev/null && echo "✓" || echo "✗ (browser tool no funcionará)"
echo -n "  Node.js:  "; command -v node &>/dev/null && echo "✓ $(node -v)" || echo "✗ (GitHub MCP no funcionará)"
echo -n "  npx:      "; command -v npx &>/dev/null && echo "✓" || echo "✗"
echo -n "  ripgrep:  "; command -v rg &>/dev/null && echo "✓" || echo "✗ (búsquedas lentas)"
echo -n "  Python:   "; python3 -c "import openhands" &>/dev/null && echo "✓ openhands-sdk" || echo "✗"

echo ""
echo "=============================================="
echo "  ✅ INSTALACIÓN COMPLETADA"
echo "  Ejecuta: python app.py"
echo "=============================================="
