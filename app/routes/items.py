from fastapi import APIRouter, Form, File, UploadFile, Request
from app.utils.files import save_optional_image
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from typing import Optional
from app.db import DB_PATH

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/add_item")
async def add_item(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    hashtags: str = Form(""),
    city: Optional[str] = Form(None),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None),
    image: UploadFile | None = File(None),
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    # Convert empty strings to None and parse valid numbers
    try:
        latitude = float(latitude) if latitude and latitude.strip() else None
    except ValueError:
        latitude = None
        
    try:
        longitude = float(longitude) if longitude and longitude.strip() else None
    except ValueError:
        longitude = None

    image_path = save_optional_image(image)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            INSERT INTO items (
                name, description, status, hashtags, owner_id,
                city, latitude, longitude, image_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, description, "available", hashtags, user_id,
            city, latitude, longitude, image_path
        ))
        conn.commit()

    return RedirectResponse(url="/", status_code=303)

@router.post("/borrow")
async def borrow_item(request: Request, item_id: int = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("UPDATE items SET status = 'borrowed' WHERE id = ?", (item_id,))
        conn.commit()

    return RedirectResponse(url="/", status_code=303)

@router.post("/delete_item")
async def delete_item(request: Request, item_id: int = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Make sure only the item's owner can delete it
        c.execute("DELETE FROM items WHERE id = ? AND owner_id = ?", (item_id, user_id))
        conn.commit()

    return RedirectResponse(url="/", status_code=303)

@router.post("/rate_item")
async def rate_item(
    request: Request,
    item_id: int = Form(...),
    condition_score: float = Form(...),
    comment: str = Form(None)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Must+be+logged+in", status_code=303)
    
    user_id = int(user_id)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Check if user has borrowed this item
        c.execute("""
            SELECT owner_id
            FROM items
            WHERE id = ? AND status = 'borrowed'
        """, (item_id,))
        item = c.fetchone()
        
        if not item or item[0] != user_id:
            return RedirectResponse(url="/?error=Can+only+rate+borrowed+items", status_code=303)

        try:
            # Update item's condition score
            c.execute("""
                UPDATE items
                SET condition_score = ?
                WHERE id = ?
            """, (condition_score, item_id))
            conn.commit()
            
            return RedirectResponse(url="/", status_code=303)
        except sqlite3.Error as e:
            return RedirectResponse(url="/?error=Rating+failed", status_code=303)
