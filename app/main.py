from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os

app = FastAPI()

# Set up template and static directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize SQLite DB
DB_PATH = os.path.join(BASE_DIR, "crowdi.db")

# def get_questions():
#     with sqlite3.connect(DB_PATH) as conn:
#         c = conn.cursor()
#         c.execute("SELECT id, text, type FROM questions ORDER BY id DESC")
#         questions = c.fetchall()
#     return questions

def get_questions(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT q.id, q.text, q.type,
            EXISTS (
                SELECT 1 FROM responses r
                WHERE r.question_id = q.id AND r.user_id = ?
            ) AS has_responded
            FROM questions q
            ORDER BY q.id DESC
        """, (user_id,))
        questions = c.fetchall()
    return questions

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Create questions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                type TEXT NOT NULL
            )
        ''')
        # Create responses table
        c.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                response TEXT NOT NULL,
                FOREIGN KEY(question_id) REFERENCES questions(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        ''')
        conn.commit()

init_db()

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        conn.commit()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = c.fetchone()[0]

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="user_id", value=str(user_id), httponly=True)
    return response

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_id = request.cookies.get("user_id")
    questions = get_questions(user_id) if user_id else get_questions()
    return templates.TemplateResponse("home.html", {
        "request": request,
        "questions": questions,
        "user_id": user_id
    })

@app.post("/ask", response_class=HTMLResponse)
async def ask_question(request: Request, text: str = Form(...), type: str = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO questions (text, type) VALUES (?, ?)", (text, type))
        conn.commit()
    user_id = request.cookies.get("user_id")
    questions = get_questions(user_id) if user_id else get_questions()
    return templates.TemplateResponse("questions.html", {"request": request, "questions": questions})

@app.get("/questions", response_class=HTMLResponse)
async def get_questions_partial(request: Request):
    questions = get_questions()
    return templates.TemplateResponse("questions.html", {"request": request, "questions": questions})

@app.post("/respond", response_class=HTMLResponse)
async def respond(request: Request, question_id: int = Form(...), response: str = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to respond.", status_code=403)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO responses (question_id, user_id, response) VALUES (?, ?, ?)", (question_id, user_id, response))
        conn.commit()
    return HTMLResponse("Thanks for responding!")

# Create template file if not exists
home_html_path = os.path.join(TEMPLATES_DIR, "home.html")
if not os.path.exists(home_html_path):
    with open(home_html_path, "w") as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Crowdi</title>
    <script src="https://unpkg.com/htmx.org@1.9.2"></script>
</head>
<body>
    <h1>Login</h1>
    <form action="/login" method="post">
        <input type="text" name="username" required placeholder="Enter your name">
        <button type="submit">Log in</button>
    </form>

    <h1>Ask a Question</h1>
    <form hx-post="/ask" hx-target="#questions" hx-swap="outerHTML">
        <input type="text" name="text" required placeholder="Your question">
        <select name="type" required>
            <option value="text">Open Text</option>
            <option value="yesno">Yes/No</option>
            <option value="multiple">Multiple Choice</option>
        </select>
        <button type="submit">Ask</button>
    </form>

    {% include "questions.html" %}
</body>
</html>
''')
