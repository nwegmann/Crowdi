from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
import sqlite3
from app.db import DB_PATH

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/add_request")
async def add_request(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            INSERT INTO requested_items (title, description, user_id)
            VALUES (?, ?, ?)
        """, (title, description, user_id))
        conn.commit()

    return RedirectResponse(url="/", status_code=303)

@router.get("/my_requests", response_class=HTMLResponse)
async def my_requests(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT r.id, r.title, r.description, r.user_id, u.username
            FROM requested_items r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id = ?
        """, (user_id,))
        my_requests = c.fetchall()

    return templates.TemplateResponse("my_requests.html", {
        "request": request,
        "my_requests": my_requests
    })

@router.get("/requests", response_class=HTMLResponse)
async def requests(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT r.id, r.title, r.description, r.user_id, u.username
            FROM requested_items r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id != ?
        """, (user_id,))
        requested_items = c.fetchall()

    return templates.TemplateResponse("requests.html", {
        "request": request,
        "requested_items": requested_items
    })
