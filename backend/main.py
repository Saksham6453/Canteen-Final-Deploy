import os
import psycopg2
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Smart Canteen API", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────────────────────────
# In production, replace "*" with your actual Vercel frontend URL
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DATABASE ──────────────────────────────────────────────────────────────────
def get_db():
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"), sslmode="require")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"), sslmode="require")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id SERIAL PRIMARY KEY,
            category TEXT,
            name TEXT,
            price REAL,
            description TEXT,
            emoji TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            username TEXT,
            items TEXT,
            total REAL,
            status TEXT,
            timestamp TEXT
        )
    """)

    # Seed menu
    cur.execute("SELECT COUNT(*) FROM menu")
    if cur.fetchone()[0] == 0:
        menu_items = [
            ("Snacks",    "Crispy French Fries",     60,  "Salted potato fries served with ketchup",         "🍟"),
            ("Snacks",    "Punjabi Samosa (2pcs)",    40,  "Hot samosas with mint and tamarind chutney",       "🥟"),
            ("Fast Food", "Margherita Pizza",        120,  "Classic cheese pizza with a thin crust",           "🍕"),
            ("Fast Food", "Aloo Tikki Burger",        70,  "Crispy patty with fresh veggies and mayo",         "🍔"),
            ("Fast Food", "White Sauce Pasta",       140,  "Creamy penne pasta with sweet corn and herbs",     "🍝"),
            ("Meals",     "Rajma Chawal Bowl",        90,  "Authentic homestyle rajma with basmati rice",      "🍛"),
            ("Meals",     "Chole Bhature (2pcs)",    100,  "Spicy punjabi chole with fluffy bhature",          "🍲"),
            ("Beverages", "Cold Coffee",              80,  "Thick blended coffee with chocolate syrup",        "🧋"),
            ("Beverages", "Fresh Lime Soda",          50,  "Refreshing sweet and salted lime drink",           "🍹"),
        ]
        for item in menu_items:
            cur.execute(
                "INSERT INTO menu (category, name, price, description, emoji) VALUES (%s,%s,%s,%s,%s)",
                item,
            )

    # Seed default users
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s,%s,%s)", ("admin", "admin", "admin"))
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s,%s,%s)", ("student", "pass", "student"))

    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"DB Init Error: {e}")

# ── SCHEMAS ───────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class CartItem(BaseModel):
    id: int
    name: str
    price: float

class CheckoutRequest(BaseModel):
    username: str
    cart: List[CartItem]

class StatusUpdate(BaseModel):
    status: str

# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.post("/api/login")
def login(body: LoginRequest, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, role FROM users WHERE username=%s AND password=%s",
        (body.username, body.password),
    )
    user = cur.fetchone()
    cur.close()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"id": user[0], "username": user[1], "role": user[2]}

# ── MENU ──────────────────────────────────────────────────────────────────────
@app.get("/api/menu")
def get_menu(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT id, category, name, price, description, emoji FROM menu")
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": r[0], "category": r[1], "name": r[2], "price": r[3], "description": r[4], "emoji": r[5]}
        for r in rows
    ]

# ── ORDERS ────────────────────────────────────────────────────────────────────
@app.post("/api/orders")
def place_order(body: CheckoutRequest, conn=Depends(get_db)):
    if not body.cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    total = sum(item.price for item in body.cart)
    items_str = ", ".join(item.name for item in body.cart)
    timestamp = datetime.now().strftime("%I:%M %p | %d %b")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (username, items, total, status, timestamp) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (body.username, items_str, total, "Pending", timestamp),
    )
    order_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return {"order_id": order_id, "status": "Pending", "total": total}

@app.get("/api/orders/{username}")
def get_user_orders(username: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, items, total, status, timestamp FROM orders WHERE username=%s ORDER BY id DESC",
        (username,),
    )
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": r[0], "username": r[1], "items": r[2], "total": r[3], "status": r[4], "timestamp": r[5]}
        for r in rows
    ]

@app.get("/api/admin/orders")
def get_all_orders(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT id, username, items, total, status, timestamp FROM orders ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": r[0], "username": r[1], "items": r[2], "total": r[3], "status": r[4], "timestamp": r[5]}
        for r in rows
    ]

@app.patch("/api/admin/orders/{order_id}")
def update_order_status(order_id: int, body: StatusUpdate, conn=Depends(get_db)):
    valid = {"Pending", "Preparing", "Ready", "Completed"}
    if body.status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status")
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (body.status, order_id))
    conn.commit()
    cur.close()
    return {"order_id": order_id, "status": body.status}

@app.get("/")
def root():
    return {"message": "Smart Canteen API is running 🍔"}
