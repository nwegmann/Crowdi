from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from app.db import DB_PATH

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/conversations", response_class=HTMLResponse)
async def conversations(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        username = row["username"] if row else None
        c.execute("""
            SELECT c.id, u.username, i.name,
                EXISTS(
                    SELECT 1
                    FROM messages m
                    WHERE m.conversation_id = c.id
                      AND m.sender_id != ?
                      AND m.seen = 0
                ) as has_unread
            FROM conversations c
            JOIN users u ON u.id = CASE
                WHEN c.user1_id = ? THEN c.user2_id
                ELSE c.user1_id
            END
            JOIN items i ON c.item_id = i.id
            WHERE c.user1_id = ? OR c.user2_id = ?
            ORDER BY c.id DESC
        """, (user_id, user_id, user_id, user_id))
        conversations = c.fetchall()

    return templates.TemplateResponse("conversations.html", {
        "username": username,
        "request": request,
        "user_id": int(user_id),
        "conversations": conversations
    })

@router.get("/conversations/{conversation_id}", response_class=HTMLResponse)
async def view_conversation(request: Request, conversation_id: int):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to view messages.", status_code=403)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("""
            SELECT m.sender_id, u.username, m.content, m.sent_at
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ?
            ORDER BY m.sent_at ASC
        """, (conversation_id,))
        messages = c.fetchall()

        c.execute("SELECT user1_id, user2_id, item_id FROM conversations WHERE id = ?", (conversation_id,))
        convo = c.fetchone()
        if not convo or int(user_id) not in convo:
            return HTMLResponse("Unauthorized", status_code=403)

        c.execute("""
            UPDATE messages
            SET seen = 1
            WHERE conversation_id = ? AND sender_id != ?
        """, (conversation_id, user_id))
        conn.commit()

        user1_id = convo["user1_id"]
        user2_id = convo["user2_id"]
        item_id = convo["item_id"]
        other_id = user1_id if int(user_id) != user1_id else user2_id
        c.execute("SELECT username FROM users WHERE id = ?", (other_id,))
        other_username = c.fetchone()["username"]

        c.execute("""
            SELECT i.id, i.name, i.description, u.username, i.hashtags, i.city, i.image_path, i.owner_id, i.status
            FROM items i
            JOIN users u ON i.owner_id = u.id
            WHERE i.id = ?
        """, (item_id,))
        item_row = c.fetchone()

        item = {
            "id": item_row["id"],
            "name": item_row["name"],
            "description": item_row["description"],
            "owner": item_row["username"],
            "hashtags": item_row["hashtags"],
            "city": item_row["city"],
            "image_path": item_row["image_path"],
            "owner_id": item_row["owner_id"],
            "status": item_row["status"]
        } if item_row else None

        # Get pending borrow requests if user is the item owner
        pending_requests = []
        if item and int(user_id) == item["owner_id"] and item["status"] == "available":
            c.execute("""
                SELECT br.requester_id, u.username, br.created_at
                FROM borrow_requests br
                JOIN users u ON br.requester_id = u.id
                WHERE br.item_id = ? AND br.status = 'pending'
            """, (item_id,))
            pending_requests = c.fetchall()

        # Get request status if user is the requester
        request_status = None
        if item and int(user_id) != item["owner_id"]:
            c.execute("""
                SELECT status, created_at
                FROM borrow_requests
                WHERE item_id = ? AND requester_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (item_id, user_id))
            request_row = c.fetchone()
            if request_row:
                request_status = {
                    "status": request_row["status"],
                    "created_at": request_row["created_at"]
                }

        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        username = row["username"] if row else None

        # Mark notifications as seen for this item if the user is the owner
        if item and int(user_id) == item["owner_id"]:
            c.execute("""
                UPDATE notifications
                SET seen = 1
                WHERE user_id = ? AND seen = 0 AND message LIKE ?
            """, (user_id, f"%{item['name']}%"))
            conn.commit()

    return templates.TemplateResponse("conversation.html", {
        "request": request,
        "user_id": int(user_id),
        "conversation_id": conversation_id,
        "messages": messages,
        "item": item,
        "other_username": other_username,
        "other_user_id": other_id,
        "username": username,
        "pending_requests": pending_requests,
        "request_status": request_status
    })

@router.post("/conversations/{conversation_id}/send")
async def send_message(
    request: Request,
    conversation_id: int,
    content: str = Form(...)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO messages (conversation_id, sender_id, content)
            VALUES (?, ?, ?)
        """, (conversation_id, user_id, content))
        conn.commit()

    return RedirectResponse(url=f"/conversations/{conversation_id}", status_code=303)

@router.post("/start_conversation", response_class=HTMLResponse)
async def start_conversation(
    request: Request,
    other_user_id: int = Form(...),
    item_id: int = Form(None)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to start a conversation.", status_code=403)

    user_id = int(user_id)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Check if conversation already exists
        c.execute('''
            SELECT id FROM conversations 
            WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
              AND item_id = ?
        ''', (user_id, other_user_id, other_user_id, user_id, item_id))
        existing = c.fetchone()

        if existing:
            conversation_id = existing["id"]
        else:
            c.execute('''
                INSERT INTO conversations (user1_id, user2_id, item_id) 
                VALUES (?, ?, ?)
            ''', (user_id, other_user_id, item_id))
            conversation_id = c.lastrowid
            conn.commit()

    return RedirectResponse(f"/conversations/{conversation_id}", status_code=303)