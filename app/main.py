from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import routers  # Import the routes from the new modularized files
import app.db as db
import os

app = FastAPI()

# Set up template and static directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Initialize database
DB_PATH = db.get_path()
db.init_db()

# Mount static files for front-end assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Jinja templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include the modularized route handlers
for router in routers:
    app.include_router(router)

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