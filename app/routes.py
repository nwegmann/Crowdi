from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import app.db as db

# Modular route imports
from app.routes import auth, items, requests, conversations, notifications

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

DB_PATH = db.get_path()

# Register modular routers
router.include_router(auth.router)
router.include_router(items.router)
router.include_router(requests.router)
router.include_router(conversations.router)
router.include_router(notifications.router)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_id = request.cookies.get("user_id")
    username = request.cookies.get("username")
    items = []
    my_items = []
    requested_items = []
    my_requests = []

    if user_id:
        try:
            user_id_int = int(user_id)
        except ValueError:
            return HTMLResponse("Invalid user ID cookie.", status_code=400)
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username, u.id
                FROM items i 
                JOIN users u ON i.owner_id = u.id 
                WHERE i.owner_id != ?
            """, (user_id_int,))
            items = c.fetchall()

            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username
                FROM items i 
                JOIN users u ON i.owner_id = u.id 
                WHERE i.owner_id = ?
            """, (user_id_int,))
            my_items = c.fetchall()

            c.execute("""
                SELECT r.id, r.title, r.description, r.user_id, u.username, r.location_name, r.latitude, r.longitude
                FROM requested_items r
                JOIN users u ON r.user_id = u.id
            """)
            requested_items = c.fetchall()

            c.execute("""
                SELECT id, title, description
                FROM requested_items
                WHERE user_id = ?
            """, (user_id,))
            my_requests = c.fetchall()

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user_id": user_id,
            "username": username,
            "items": items,
            "my_items": my_items,
            "requested_items": requested_items,
            "my_requests": my_requests
        }
    )