from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from app.db import DB_PATH

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/notifications", response_class=HTMLResponse)
async def check_notifications(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Unread messages
        c.execute("""
            SELECT COUNT(*)
            FROM messages
            WHERE conversation_id IN (
                SELECT id FROM conversations WHERE user1_id = ? OR user2_id = ?
            )
            AND sender_id != ?
            AND seen = 0
        """, (user_id, user_id, user_id))
        msg_count = c.fetchone()[0]
        # Unseen notifications
        c.execute("""
            SELECT COUNT(*) FROM notifications WHERE user_id = ? AND seen = 0
        """, (user_id,))
        notif_count = c.fetchone()[0]

    if msg_count > 0 or notif_count > 0:
        return templates.TemplateResponse("notification_snippet.html", {"request": request})
    return HTMLResponse("")