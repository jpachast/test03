#!/bin/bash
# Script de instalación para OpenHands Chat
# Ejecutar: ./install.sh

echo "🚀 Instalando OpenHands Chat..."
echo ""

# Instalar dependencias de Python
echo "📦 Instalando dependencias Python..."
pip install -q -r requirements.txt

echo ""
echo "✅ Instalación completada!"
echo ""
echo "Para iniciar la aplicación:"
echo "  python app.py"
echo ""
echo "O con el script:"
echo "  ./start.sh"
echo ""
echo "NOTA: La app auto-instala todo lo necesario al iniciar."
echo "      Solo ejecuta 'python app.py' y listo."
