"""
Inventory Management System - Main Application
FastAPI backend with SQLite database
"""
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import sqlite3
import hashlib
import jwt
import json
from pathlib import Path

# Configuration
SECRET_KEY = "inventory-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
DATABASE = "data/inventory.db"

app = FastAPI(title="Inventory Management System", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security
security = HTTPBearer(auto_error=False)

# ============== DATABASE ==============
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    Path("data").mkdir(exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            sku TEXT UNIQUE,
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 5,
            category_id INTEGER,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Stock movements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            notes TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_email TEXT,
            status TEXT DEFAULT 'pending',
            total REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Order items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Create default admin user
    admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            ("admin", admin_pass, "admin@inventory.com", "admin")
        )
    except sqlite3.IntegrityError:
        pass
    
    # Create sample categories
    sample_categories = [
        ("Electrónicos", "Dispositivos electrónicos y gadgets"),
        ("Ropa", "Prendas de vestir"),
        ("Alimentos", "Productos alimenticios"),
        ("Hogar", "Artículos para el hogar"),
    ]
    for name, desc in sample_categories:
        try:
            cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)", (name, desc))
        except:
            pass
    
    # Create sample products
    sample_products = [
        ("Laptop HP", "Laptop HP 15 pulgadas", "LAP-001", 899.99, 15, 3, 1),
        ("Mouse Logitech", "Mouse inalámbrico", "MOU-001", 29.99, 50, 10, 1),
        ("Teclado Mecánico", "Teclado RGB", "TEC-001", 79.99, 25, 5, 1),
        ("Camiseta Básica", "Camiseta algodón", "CAM-001", 19.99, 100, 20, 2),
        ("Pantalón Jeans", "Jeans clásico", "PAN-001", 49.99, 60, 15, 2),
        ("Arroz Premium", "Arroz 1kg", "ARR-001", 2.99, 200, 50, 3),
        ("Aceite de Oliva", "Aceite extra virgen", "ACE-001", 8.99, 80, 20, 3),
        ("Lámpara LED", "Lámpara de escritorio", "LAM-001", 24.99, 40, 10, 4),
    ]
    for name, desc, sku, price, stock, min_stock, cat_id in sample_products:
        try:
            cursor.execute(
                "INSERT INTO products (name, description, sku, price, stock, min_stock, category_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, desc, sku, price, stock, min_stock, cat_id)
            )
        except:
            pass
    
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# ============== MODELS ==============
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    price: float = 0
    stock: int = 0
    min_stock: int = 5
    category_id: Optional[int] = None

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MovementCreate(BaseModel):
    product_id: int
    type: str  # 'in' or 'out'
    quantity: int
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    items: List[dict]  # [{product_id, quantity}]
    notes: Optional[str] = None

# ============== AUTH ==============
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ============== AUTH ENDPOINTS ==============
@app.post("/api/login")
async def login(user: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    cursor.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
        (user.username, password_hash)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token = create_token({"user_id": row["id"], "username": row["username"], "role": row["role"]})
    return {"token": token, "user": {"id": row["id"], "username": row["username"], "role": row["role"]}}

@app.get("/api/me")
async def get_me(user = Depends(verify_token)):
    return user

# ============== USERS CRUD ==============
@app.get("/api/users")
async def list_users(user = Depends(verify_token)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, created_at FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/users")
async def create_user(data: UserCreate, user = Depends(verify_token)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    conn = get_db()
    cursor = conn.cursor()
    password_hash = hashlib.sha256(data.password.encode()).hexdigest()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            (data.username, password_hash, data.email, data.role)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    finally:
        conn.close()
    return {"id": user_id, "username": data.username}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, user = Depends(verify_token)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ============== CATEGORIES CRUD ==============
@app.get("/api/categories")
async def list_categories(user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/categories")
async def create_category(data: CategoryCreate, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO categories (name, description) VALUES (?, ?)",
        (data.name, data.description)
    )
    conn.commit()
    cat_id = cursor.lastrowid
    conn.close()
    return {"id": cat_id, "name": data.name}

@app.put("/api/categories/{cat_id}")
async def update_category(cat_id: int, data: CategoryCreate, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE categories SET name = ?, description = ? WHERE id = ?",
        (data.name, data.description, cat_id)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/api/categories/{cat_id}")
async def delete_category(cat_id: int, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ============== PRODUCTS CRUD ==============
@app.get("/api/products")
async def list_products(user = Depends(verify_token), category_id: Optional[int] = None, search: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (p.name LIKE ? OR p.sku LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY p.name"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/products/{product_id}")
async def get_product(product_id: int, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """, (product_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return dict(row)

@app.post("/api/products")
async def create_product(data: ProductCreate, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (name, description, sku, price, stock, min_stock, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data.name, data.description, data.sku, data.price, data.stock, data.min_stock, data.category_id))
        conn.commit()
        product_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="SKU ya existe")
    finally:
        conn.close()
    return {"id": product_id, "name": data.name}

@app.put("/api/products/{product_id}")
async def update_product(product_id: int, data: ProductCreate, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products SET 
            name = ?, description = ?, sku = ?, price = ?, 
            stock = ?, min_stock = ?, category_id = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (data.name, data.description, data.sku, data.price, data.stock, data.min_stock, data.category_id, product_id))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ============== STOCK MOVEMENTS ==============
@app.get("/api/movements")
async def list_movements(user = Depends(verify_token), product_id: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT m.*, p.name as product_name, u.username
        FROM movements m
        JOIN products p ON m.product_id = p.id
        LEFT JOIN users u ON m.user_id = u.id
    """
    params = []
    if product_id:
        query += " WHERE m.product_id = ?"
        params.append(product_id)
    query += " ORDER BY m.created_at DESC LIMIT 100"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/movements")
async def create_movement(data: MovementCreate, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current stock
    cursor.execute("SELECT stock FROM products WHERE id = ?", (data.product_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    current_stock = row["stock"]
    if data.type == "in":
        new_stock = current_stock + data.quantity
    else:
        new_stock = current_stock - data.quantity
        if new_stock < 0:
            raise HTTPException(status_code=400, detail="Stock insuficiente")
    
    # Create movement
    cursor.execute("""
        INSERT INTO movements (product_id, type, quantity, notes, user_id)
        VALUES (?, ?, ?, ?, ?)
    """, (data.product_id, data.type, data.quantity, data.notes, user["user_id"]))
    
    # Update stock
    cursor.execute("UPDATE products SET stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                   (new_stock, data.product_id))
    
    conn.commit()
    movement_id = cursor.lastrowid
    conn.close()
    return {"id": movement_id, "new_stock": new_stock}

# ============== ORDERS ==============
@app.get("/api/orders")
async def list_orders(user = Depends(verify_token), status: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM orders"
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/orders/{order_id}")
async def get_order(order_id: int, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    cursor.execute("""
        SELECT oi.*, p.name as product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,))
    items = cursor.fetchall()
    conn.close()
    
    result = dict(order)
    result["items"] = [dict(item) for item in items]
    return result

@app.post("/api/orders")
async def create_order(data: OrderCreate, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Calculate total and validate stock
    total = 0
    for item in data.items:
        cursor.execute("SELECT price, stock FROM products WHERE id = ?", (item["product_id"],))
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail=f"Producto {item['product_id']} no encontrado")
        if product["stock"] < item["quantity"]:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para producto {item['product_id']}")
        total += product["price"] * item["quantity"]
    
    # Create order
    cursor.execute("""
        INSERT INTO orders (customer_name, customer_email, total, notes)
        VALUES (?, ?, ?, ?)
    """, (data.customer_name, data.customer_email, total, data.notes))
    order_id = cursor.lastrowid
    
    # Create order items and update stock
    for item in data.items:
        cursor.execute("SELECT price FROM products WHERE id = ?", (item["product_id"],))
        price = cursor.fetchone()["price"]
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, item["product_id"], item["quantity"], price))
        
        # Update stock
        cursor.execute("""
            UPDATE products SET stock = stock - ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (item["quantity"], item["product_id"]))
    
    conn.commit()
    conn.close()
    return {"id": order_id, "total": total}

@app.put("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str, user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (status, order_id))
    conn.commit()
    conn.close()
    return {"ok": True}

# ============== DASHBOARD ==============
@app.get("/api/dashboard")
async def get_dashboard(user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Total products
    cursor.execute("SELECT COUNT(*) as count FROM products")
    total_products = cursor.fetchone()["count"]
    
    # Low stock products
    cursor.execute("SELECT COUNT(*) as count FROM products WHERE stock <= min_stock")
    low_stock = cursor.fetchone()["count"]
    
    # Total categories
    cursor.execute("SELECT COUNT(*) as count FROM categories")
    total_categories = cursor.fetchone()["count"]
    
    # Total orders
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cursor.fetchone()["count"]
    
    # Pending orders
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'")
    pending_orders = cursor.fetchone()["count"]
    
    # Total inventory value
    cursor.execute("SELECT SUM(price * stock) as value FROM products")
    inventory_value = cursor.fetchone()["value"] or 0
    
    # Recent movements
    cursor.execute("""
        SELECT m.*, p.name as product_name
        FROM movements m
        JOIN products p ON m.product_id = p.id
        ORDER BY m.created_at DESC LIMIT 5
    """)
    recent_movements = [dict(row) for row in cursor.fetchall()]
    
    # Low stock products list
    cursor.execute("""
        SELECT id, name, stock, min_stock FROM products 
        WHERE stock <= min_stock ORDER BY stock ASC LIMIT 5
    """)
    low_stock_products = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_products": total_products,
        "low_stock": low_stock,
        "total_categories": total_categories,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "inventory_value": round(inventory_value, 2),
        "recent_movements": recent_movements,
        "low_stock_products": low_stock_products
    }

# ============== FRONTEND ==============
@app.get("/", response_class=HTMLResponse)
async def index():
    return Path("templates/index.html").read_text()

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12001)
