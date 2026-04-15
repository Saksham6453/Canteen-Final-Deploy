# 🍔 Smart Canteen – FastAPI + Vanilla JS

**K.R. Mangalam University | Academic Year 2025-26**

Separated into two independently deployable parts:
- `backend/` → FastAPI (deploy to **Render**)
- `frontend/` → Plain HTML/CSS/JS (deploy to **Vercel**)

---

## Project Structure

```
smart-canteen-v2/
├── backend/
│   ├── main.py            # FastAPI app + all routes
│   ├── requirements.txt
│   ├── Procfile           # For Render
│   └── .env.example
└── frontend/
    ├── index.html         # Login page
    ├── vercel.json
    ├── css/
    │   └── style.css
    ├── js/
    │   └── config.js      # ← Set your backend URL here
    └── pages/
        ├── menu.html
        ├── cart.html
        ├── orders.html
        └── admin.html
```

---

## Deployment Guide

### Step 1 – Set up a free PostgreSQL database

Go to [neon.tech](https://neon.tech) → Create project → Copy the **connection string**.
It looks like: `postgresql://user:pass@host.neon.tech/dbname`

---

### Step 2 – Deploy Backend to Render

1. Push the `backend/` folder to a **new GitHub repo** (e.g. `smart-canteen-backend`)
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect the GitHub repo
4. Set these fields:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. Add **Environment Variables**:
   - `POSTGRES_URL` → your Neon connection string
6. Click **Deploy**
7. Copy your Render URL (e.g. `https://smart-canteen-backend.onrender.com`)

---

### Step 3 – Update Frontend Config

Open `frontend/js/config.js` and replace the URL:

```js
const API_BASE = "https://smart-canteen-backend.onrender.com";
```

---

### Step 4 – Deploy Frontend to Vercel

1. Push the `frontend/` folder to a **new GitHub repo** (e.g. `smart-canteen-frontend`)
2. Go to [vercel.com](https://vercel.com) → **Add New Project** → import repo
3. **Framework Preset:** Other (no build needed)
4. Click **Deploy**
5. Copy your Vercel URL (e.g. `https://smart-canteen.vercel.app`)

---

### Step 5 – Update CORS on Backend

Go to Render → your backend service → **Environment Variables** → add:

- `ALLOWED_ORIGINS` → `https://smart-canteen.vercel.app`

Redeploy the backend. Done! ✅

---

## Default Credentials

| Role    | Username | Password |
|---------|----------|----------|
| Student | student  | pass     |
| Admin   | admin    | admin    |

---

## API Endpoints

| Method | Endpoint                          | Description              |
|--------|-----------------------------------|--------------------------|
| POST   | `/api/login`                      | Login                    |
| GET    | `/api/menu`                       | Get all menu items       |
| POST   | `/api/orders`                     | Place an order           |
| GET    | `/api/orders/{username}`          | Get orders for a student |
| GET    | `/api/admin/orders`               | Get all orders (admin)   |
| PATCH  | `/api/admin/orders/{id}`          | Update order status      |
