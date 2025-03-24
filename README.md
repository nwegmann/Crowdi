# Crowdi

Crowdi is a lightweight, location-based polling app built with **FastAPI**, **SQLite**, and **HTMX**. Quickly ask questions, create polls, and get real-time responses.

---

## 🚀 Features

- Simple authentication
- Multiple question types (open text, yes/no, multiple-choice)
- Real-time updates with HTMX
- Lightweight SQLite database

---

## 🛠 Tech Stack

- FastAPI
- SQLite
- Jinja2
- HTMX

---

## 📦 Setup

```bash
git clone git@github.com:nwegmann/crowdi.git
cd crowdi
python3 -m venv .venv
source .venv/bin/activate
uv pip install -e .
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

---

## 📂 Project Structure

```
crowdi/
├── app/
│   ├── main.py
│   ├── templates/
│   └── static/
├── crowdi.db
├── pyproject.toml
└── .gitignore
```

---

## ⚡️ Contributing

Feel free to submit pull requests or open issues.

---

## 📜 License

MIT

