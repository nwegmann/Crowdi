from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import bcrypt
from app.db import DB_PATH

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def update_trust_score(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Calculate average rating
        c.execute("""
            SELECT AVG(rating) as avg_rating
            FROM user_ratings
            WHERE rated_id = ?
        """, (user_id,))
        result = c.fetchone()
        avg_rating = result[0] if result[0] is not None else 5.0
        
        # Update user's trust score
        c.execute("""
            UPDATE users
            SET trust_score = ?
            WHERE id = ?
        """, (avg_rating, user_id))
        conn.commit()

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
            return RedirectResponse(url="/?error=User+not+found", status_code=303)

@router.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return RedirectResponse(url="/?error=Passwords+do+not+match", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Check if username already exists
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        if c.fetchone():
            return RedirectResponse(url="/?error=Username+already+exists", status_code=303)

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

@router.post("/rate_user")
async def rate_user(
    request: Request,
    rated_id: int = Form(...),
    rating: float = Form(...),
    comment: str = Form(None)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Must+be+logged+in", status_code=303)
    
    user_id = int(user_id)
    if user_id == rated_id:
        return RedirectResponse(url="/?error=Cannot+rate+yourself", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        try:
            c.execute("""
                INSERT OR REPLACE INTO user_ratings (rater_id, rated_id, rating, comment)
                VALUES (?, ?, ?, ?)
            """, (user_id, rated_id, rating, comment))
            conn.commit()
            
            # Update the rated user's trust score
            update_trust_score(rated_id)
            
            return RedirectResponse(url=f"/user/{rated_id}", status_code=303)
        except sqlite3.Error as e:
            return RedirectResponse(url="/?error=Rating+failed", status_code=303)

@router.get("/user/{user_id}", response_class=HTMLResponse)
async def user_profile(request: Request, user_id: int):
    current_user_id = request.cookies.get("user_id")
    current_user_id = int(current_user_id) if current_user_id and current_user_id.isdigit() else None

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get current user's username if logged in
        current_username = None
        if current_user_id:
            c.execute("SELECT username FROM users WHERE id = ?", (current_user_id,))
            row = c.fetchone()
            if row:
                current_username = row["username"]
        
        # Get user info
        c.execute("""
            SELECT id, username, trust_score, created_at
            FROM users
            WHERE id = ?
        """, (user_id,))
        user = c.fetchone()
        
        if not user:
            return RedirectResponse(url="/?error=User+not+found", status_code=303)
        
        # Get user's ratings
        c.execute("""
            SELECT r.rating, r.comment, r.created_at, u.username as rater_username
            FROM user_ratings r
            JOIN users u ON r.rater_id = u.id
            WHERE r.rated_id = ?
            ORDER BY r.created_at DESC
        """, (user_id,))
        ratings = c.fetchall()

    return templates.TemplateResponse("user_profile.html", {
        "request": request,
        "user": user,
        "ratings": ratings,
        "user_id": current_user_id,
        "username": current_username
    })

@router.post("/delete_account")
async def delete_account(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Delete user's items
        c.execute("DELETE FROM items WHERE owner_id = ?", (user_id,))
        
        # Delete user's requested items
        c.execute("DELETE FROM requested_items WHERE user_id = ?", (user_id,))
        
        # Delete user's messages
        c.execute("""
            DELETE FROM messages 
            WHERE sender_id = ? 
            OR conversation_id IN (
                SELECT id FROM conversations 
                WHERE user1_id = ? OR user2_id = ?
            )
        """, (user_id, user_id, user_id))
        
        # Delete user's conversations
        c.execute("DELETE FROM conversations WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        
        # Finally, delete the user
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()

    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response
