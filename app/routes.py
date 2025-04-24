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
    requested_items = []
    my_requests = []
    
    # Debugging: Print user_id to check its value
    print(f"User ID: {user_id}")

    if user_id:
        try:
            user_id_int = int(user_id)
        except ValueError:
            return HTMLResponse("Invalid user ID cookie.", status_code=400)

        # Debugging: Ensure user_id_int is correct
        print(f"User ID (as integer): {user_id_int}")    

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
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username, u.id
                FROM items i 
                JOIN users u ON i.owner_id = u.id 
                WHERE i.owner_id != ?
            """, (user_id_int,))
            items = c.fetchall()
            print("Available items for user:", items)

            # Debugging: Print available items for user
            print(f"Available items for user: {items}")
            
            # Get user's own items
            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, u.username
                FROM items i 
                JOIN users u ON i.owner_id = u.id 
                WHERE i.owner_id = ?
            """, (user_id_int,))
            my_items = c.fetchall()
            print("User's items:", my_items)

            # Get requested items
            c.execute("""
                SELECT r.id, r.title, r.description, r.user_id, u.username, r.location_name, r.latitude, r.longitude
                FROM requested_items r
                JOIN users u ON r.user_id = u.id
            """)
            requested_items = c.fetchall()

            c.execute("""
                SELECT id, title, description
                FROM requested_items
                WHERE user_id = ?
            """, (user_id,))
            my_requests = c.fetchall()
    
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user_id": user_id,
            "username": username,
            "items": items,
            "my_items": my_items,
            "requested_items": requested_items,
            "my_requests": my_requests
        }
    )

@router.post("/add_item", response_class=HTMLResponse)
async def add_item(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    hashtags: str = Form(...),
    location_mode: str = Form(...),
    manual_location: str = Form(None),
    latitude: str = Form(None),
    longitude: str = Form(None)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to add items.", status_code=403)

    if location_mode == "manual":
        location_name = manual_location
        latitude_val = None
        longitude_val = None
    else:
        location_name = "GPS Location"
        latitude_val = float(latitude) if latitude else None
        longitude_val = float(longitude) if longitude else None

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO items (owner_id, name, description, hashtags, location_name, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, description, hashtags, location_name, latitude_val, longitude_val)
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

@router.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user_id")
    response.delete_cookie("username")
    return response

@router.get("/conversations", response_class=HTMLResponse)
async def list_conversations(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to view conversations.", status_code=403)

    # Fetch username for context
    username = None
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT c.id, u1.username, u2.username, c.created_at, c.user1_id, c.user2_id
            FROM conversations c
            JOIN users u1 ON c.user1_id = u1.id
            JOIN users u2 ON c.user2_id = u2.id
            WHERE c.user1_id = ? OR c.user2_id = ?
            ORDER BY c.created_at DESC
        """, (user_id, user_id))
        rows = c.fetchall()

        conversations = []
        for convo_id, u1, u2, created_at, user1_id, user2_id in rows:
            c.execute("""
                SELECT COUNT(*) FROM messages
                WHERE conversation_id = ? AND recipient_id = ? AND seen = 0
            """, (convo_id, user_id))
            unread_count = c.fetchone()[0]
            has_unread = unread_count > 0
            # Try to get item name from items or requested_items
            c.execute("SELECT name FROM items WHERE id = (SELECT item_id FROM conversations WHERE id = ?)", (convo_id,))
            item = c.fetchone()
            if not item:
                c.execute("SELECT title FROM requested_items WHERE id = (SELECT item_id FROM conversations WHERE id = ?)", (convo_id,))
                item = c.fetchone()
            item_name = item[0] if item else None
            conversations.append({
                "id": convo_id,
                "user1": user1_id,
                "user2": user2_id,
                "username1": u1,
                "username2": u2,
                "created_at": created_at,
                "has_unread": has_unread,
                "item_name": item_name
            })

        # Get username
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if row:
            username = row[0]

    return templates.TemplateResponse("conversations.html", {
        "request": request,
        "conversations": conversations,
        "user_id": int(user_id),
        "username": username
    })

# Route to create or fetch a conversation between two users regarding an item
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
        c = conn.cursor()
        # Check if conversation already exists
        c.execute('''
            SELECT id FROM conversations 
            WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
              AND item_id = ?
        ''', (user_id, other_user_id, other_user_id, user_id, item_id))
        existing = c.fetchone()

        if existing:
            conversation_id = existing[0]
        else:
            c.execute('''
                INSERT INTO conversations (user1_id, user2_id, item_id) 
                VALUES (?, ?, ?)
            ''', (user_id, other_user_id, item_id))
            conversation_id = c.lastrowid
            conn.commit()

    return RedirectResponse(f"/conversations/{conversation_id}", status_code=303)


@router.get("/conversations/{conversation_id}", response_class=HTMLResponse)
async def view_conversation(request: Request, conversation_id: int):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to view messages.", status_code=403)

    # Fetch username for context
    username = None
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # Get conversation info
        c.execute("SELECT user1_id, user2_id, item_id FROM conversations WHERE id = ?", (conversation_id,))
        convo = c.fetchone()
        if not convo or int(user_id) not in convo:
            return HTMLResponse("Unauthorized", status_code=403)

        # Mark messages as seen for this user
        c.execute("""
            UPDATE messages
            SET seen = 1
            WHERE conversation_id = ? AND recipient_id = ?
        """, (conversation_id, user_id))

        # Get messages
        c.execute("""
            SELECT m.sender_id, u.username, m.content, m.sent_at
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ?
            ORDER BY m.sent_at ASC
        """, (conversation_id,))
        messages = c.fetchall()

        user1_id, user2_id, item_id = convo

        # Determine the other participant's username
        other_id = user1_id if int(user_id) != user1_id else user2_id
        c.execute("SELECT username FROM users WHERE id = ?", (other_id,))
        other_username = c.fetchone()[0]

        # Try to get item from items table
        c.execute("""
            SELECT i.name, i.description, u.username
            FROM items i
            JOIN users u ON i.owner_id = u.id
            WHERE i.id = ?
        """, (item_id,))
        item_row = c.fetchone()

        # If not found, try requested_items table
        if item_row:
            item = {
                "name": item_row[0],
                "description": item_row[1],
                "owner": item_row[2]
            }
        else:
            c.execute("""
                SELECT r.title, r.description, u.username
                FROM requested_items r
                JOIN users u ON r.user_id = u.id
                WHERE r.id = ?
            """, (item_id,))
            request_row = c.fetchone()
            item = {
                "name": request_row[0],
                "description": request_row[1],
                "owner": request_row[2]
            } if request_row else None

        # Get username for the logged-in user
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if row:
            username = row[0]

    return templates.TemplateResponse("conversation.html", {
        "request": request,
        "user_id": int(user_id),
        "conversation_id": conversation_id,
        "messages": messages,
        "item": item,
        "other_username": other_username,
        "username": username
    })

# Route to handle sending a message in a conversation
@router.post("/conversations/{conversation_id}/send", response_class=HTMLResponse)
async def send_message(request: Request, conversation_id: int, content: str = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to send messages.", status_code=403)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Get the recipient from the conversation
        c.execute("SELECT user1_id, user2_id FROM conversations WHERE id = ?", (conversation_id,))
        user1_id, user2_id = c.fetchone()
        recipient_id = user2_id if int(user_id) == user1_id else user1_id

        # Insert message with recipient and unseen status
        c.execute("""
            INSERT INTO messages (conversation_id, sender_id, recipient_id, content, seen)
            VALUES (?, ?, ?, ?, 0)
        """, (conversation_id, user_id, recipient_id, content))
        conn.commit()

    return RedirectResponse(f"/conversations/{conversation_id}", status_code=303)

@router.post("/add_request", response_class=HTMLResponse)
async def add_request(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location_mode: str = Form(...),
    manual_location: str = Form(None),
    latitude: str = Form(None),
    longitude: str = Form(None)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to request items.", status_code=403)

    if location_mode == "manual":
        location_name = manual_location
        latitude_val = None
        longitude_val = None
    else:
        location_name = "GPS Location"
        latitude_val = float(latitude) if latitude else None
        longitude_val = float(longitude) if longitude else None

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO requested_items (user_id, title, description, location_name, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, title, description, location_name, latitude_val, longitude_val)
        )
        conn.commit()

    return RedirectResponse("/", status_code=303)

@router.get("/notifications", response_class=HTMLResponse)
async def check_notifications(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("")

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM messages
            WHERE recipient_id = ? AND seen = 0
        """, (user_id,))
        count = c.fetchone()[0]

    if count > 0:
        return templates.TemplateResponse("notification_snippet.html", {"request": request})
    return HTMLResponse("")