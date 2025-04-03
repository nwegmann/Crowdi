from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from . import service
import app.db as db
import sqlite3
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
    return response

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_id = request.cookies.get("user_id")
    questions = service.get_questions_with_data(user_id)
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": user_id,
        "questions": questions
    })

@router.post("/ask", response_class=HTMLResponse)
async def ask_question(request: Request, text: str = Form(...), type: str = Form(...), options: str = Form("")):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        print("we are here")
        c.execute("INSERT INTO questions (text, type) VALUES (?, ?)", (text, type))
        question_id = c.lastrowid
        
        if type == "multiple" and options:
            option_list = [opt.strip() for opt in options.split(",") if opt.strip()]
            c.executemany(
                "INSERT INTO options (question_id, option_text) VALUES (?, ?)",
                [(question_id, opt) for opt in option_list]
            )

        conn.commit()

    user_id = request.cookies.get("user_id")
    questions = db.get_questions(user_id) if user_id else db.get_questions()
    return templates.TemplateResponse("questions.html", {
        "request": request,
        "questions": questions,
        "user_id": user_id
    })

@router.post("/respond", response_class=HTMLResponse)
async def respond(request: Request, question_id: int = Form(...), response: str = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return HTMLResponse("You must be logged in to respond.", status_code=403)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO responses (question_id, user_id, response) VALUES (?, ?, ?)",
            (question_id, user_id, response)
        )
        conn.commit()

    return HTMLResponse(f"<p><strong>Your response:</strong> {response}</p>")