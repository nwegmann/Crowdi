from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
import sqlite3
import bcrypt
from app.db import DB_PATH

router = APIRouter()

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        row = c.fetchone()

        if row:
            user_id, hashed_pw = row
            if hashed_pw and bcrypt.checkpw(password.encode(), hashed_pw.encode()):
                response = RedirectResponse(url="/", status_code=303)
                response.set_cookie(key="user_id", value=str(user_id))
                return response
            else:
                return RedirectResponse(url="/?error=Invalid+credentials", status_code=303)
        else:
            # Create new user with hashed password
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            user_id = c.lastrowid
            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(key="user_id", value=str(user_id))
            return response

@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response
