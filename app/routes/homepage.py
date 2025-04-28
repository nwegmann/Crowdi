from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from app.db import DB_PATH

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_id = request.cookies.get("user_id")
    user_id_int = int(user_id) if user_id and user_id.isdigit() else None
    username = None

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        search_query = request.query_params.get("search", "")
        if search_query:
            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username, i.owner_id
                FROM items i
                JOIN users u ON i.owner_id = u.id
                WHERE (i.owner_id != ?)
                AND (i.name LIKE ? OR i.description LIKE ? OR i.hashtags LIKE ?)
            """, (user_id_int if user_id_int else -1, f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username, i.owner_id
                FROM items i
                JOIN users u ON i.owner_id = u.id
                WHERE i.owner_id != ?
            """, (user_id_int if user_id_int else -1,))
        items = c.fetchall()

        c.execute("""
            SELECT r.id, r.title, r.description, r.hashtags, r.user_id, u.username
            FROM requested_items r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id != ?
        """, (user_id_int if user_id_int else -1,))
        requested_items = c.fetchall()

        my_requests = []
        my_items = []
        if user_id_int:
            c.execute("""
                SELECT r.id, r.title, r.description, r.hashtags, r.user_id, u.username
                FROM requested_items r
                JOIN users u ON r.user_id = u.id
                WHERE r.user_id = ?
            """, (user_id_int,))
            my_requests = c.fetchall()

            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username
                FROM items i
                JOIN users u ON i.owner_id = u.id
                WHERE i.owner_id = ?
            """, (user_id_int,))
            my_items = c.fetchall()

            c.execute("SELECT username FROM users WHERE id = ?", (user_id_int,))
            row = c.fetchone()
            if row:
                username = row["username"]

    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": user_id_int,
        "username": username,
        "items": items,
        "requested_items": requested_items,
        "my_requests": my_requests,
        "my_items": my_items,
    })