

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
import sqlite3
from typing import Optional
from app.db import DB_PATH

router = APIRouter()

@router.post("/add_item")
async def add_item(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    hashtags: str = Form(""),
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO items (name, description, status, hashtags, owner_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, "available", hashtags, user_id))
        conn.commit()

    return RedirectResponse(url="/", status_code=303)

@router.post("/borrow")
async def borrow_item(request: Request, item_id: int = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE items SET status = 'borrowed' WHERE id = ?", (item_id,))
        conn.commit()

    return RedirectResponse(url="/", status_code=303)