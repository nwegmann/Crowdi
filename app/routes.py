from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import app.db as db
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

DB_PATH = db.get_path()

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        conn.commit()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = c.fetchone()[0]

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="user_id", value=str(user_id), httponly=True)
    response.set_cookie(key="username", value=username)
    return response

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_id = request.cookies.get("user_id")
    username = request.cookies.get("username")
    items = []
    my_items = []
    
    if user_id:
        try:
            user_id_int = int(user_id)
        except ValueError:
            return HTMLResponse("Invalid user ID cookie.", status_code=400)
            
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Debug: Print column names
            c.execute("PRAGMA table_info(items)")
            columns = [column[1] for column in c.fetchall()]
            print("Columns in items table:", columns)
            
            # Debug: Print all items in database
            c.execute("SELECT * FROM items")
            all_items = c.fetchall()
            print("All items in database:", all_items)
            
            # Get available items from other users
            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username
                FROM items i 
                JOIN users u ON i.owner_id = u.id 
                WHERE i.owner_id != ?
            """, (user_id_int,))
            items = c.fetchall()
            print("Available items for user:", items)
            
            # Get user's own items
            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username
                FROM items i 
                JOIN users u ON i.owner_id = u.id 
                WHERE i.owner_id = ?
            """, (user_id_int,))
            my_items = c.fetchall()
            print("User's items:", my_items)
    
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user_id": user_id,
            "username": username,
            "items": items,
            "my_items": my_items
        }
    )

@router.post("/add_item", response_class=HTMLResponse)
async def add_item(
    request: Request, 
    name: str = Form(...), 
    description: str = Form(...),
    hashtags: str = Form(...)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to add items.", status_code=403)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO items (owner_id, name, description, hashtags) VALUES (?, ?, ?, ?)",
            (user_id, name, description, hashtags)
        )
        conn.commit()

    return RedirectResponse("/", status_code=303)

@router.post("/borrow", response_class=HTMLResponse)
async def borrow_item(request: Request, item_id: int = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to borrow items.", status_code=403)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO lendings (item_id, borrower_id) VALUES (?, ?)",
            (item_id, user_id)
        )
        c.execute(
            "UPDATE items SET status = 'borrowed' WHERE id = ?",
            (item_id,)
        )
        conn.commit()

    return RedirectResponse("/", status_code=303)