# Inventory Management System

Sistema completo de gestión de inventario con:

- **Backend**: FastAPI + SQLite
- **Frontend**: HTML5 + Bootstrap 5 + JavaScript
- **Autenticación**: JWT
- **CRUDs**: Productos, Categorías, Usuarios, Órdenes, Movimientos de Stock

## Características

- 📦 Gestión de productos con SKU, precios y stock
- 📁 Categorías para organizar productos
- 📊 Dashboard con métricas en tiempo real
- 🔔 Alertas de stock bajo
- 📋 Registro de movimientos de inventario
- 🛒 Sistema de órdenes
- 👥 Gestión de usuarios con roles

## Instalación

```bash
pip install -r requirements.txt
python app.py
```

## Credenciales por defecto

- Usuario: `admin`
- Contraseña: `admin123`

## API Endpoints

- `POST /api/login` - Autenticación
- `GET /api/dashboard` - Métricas del dashboard
- `GET/POST/PUT/DELETE /api/products` - CRUD de productos
- `GET/POST/PUT/DELETE /api/categories` - CRUD de categorías
- `GET/POST /api/movements` - Movimientos de stock
- `GET/POST /api/orders` - Órdenes
- `GET/POST/DELETE /api/users` - Usuarios (solo admin)
