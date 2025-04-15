from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import router as route_handlers
import app.db as db
import sqlite3
import os

app = FastAPI()

# Set up template and static directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

DB_PATH = db.get_path()
db.init_db()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.include_router(route_handlers)

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
