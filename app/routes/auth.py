from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
import sqlite3
from app.db import DB_PATH

router = APIRouter()

@router.post("/login")
async def login(username: str = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            user_id = c.lastrowid
        else:
            user_id = row[0]

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user_id))
    return response

@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response
