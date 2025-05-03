from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from app.db import DB_PATH
from app.data.cities import CITIES
import math

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_id = request.cookies.get("user_id")
    user_id_int = int(user_id) if user_id and user_id.isdigit() else None
    username = None
    requested_items = []
    items = []

    search_query = request.query_params.get("search", "")
    tab = request.query_params.get("tab", "borrow") 
    origin_city = request.query_params.get("origin_city")
    radius_km   = float(request.query_params.get("radius", 0) or 0)
    origin_coords = CITIES.get(origin_city) if origin_city else None

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0  # km
        phi1, phi2 = math.radians(lat1), math.radians(lon1)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if tab == "borrow":
            if search_query:
                c.execute("""
                    SELECT i.id, i.name, i.description, i.status, i.hashtags, i.image_path, u.username, i.owner_id, i.city, i.latitude, i.longitude
                    FROM items i
                    JOIN users u ON i.owner_id = u.id
                    WHERE (i.owner_id != ?)
                    AND (i.name LIKE ? OR i.description LIKE ? OR i.hashtags LIKE ?)
                """, (user_id_int if user_id_int else -1, f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
            else:
                c.execute("""
                    SELECT i.id, i.name, i.description, i.status, i.hashtags, i.image_path, u.username, i.owner_id, i.city, i.latitude, i.longitude
                    FROM items i
                    JOIN users u ON i.owner_id = u.id
                    WHERE i.owner_id != ?
                """, (user_id_int if user_id_int else -1,))
            items = c.fetchall()
            if origin_coords and radius_km > 0:
                lat0, lon0 = origin_coords["lat"], origin_coords["lng"]
                items = [
                    row for row in items
                    if row["latitude"] and row["longitude"] and
                    haversine(lat0, lon0, row["latitude"], row["longitude"]) <= radius_km
                ]
        elif tab == "requests":
            if search_query:
                c.execute("""
                    SELECT r.id, r.title, r.description, r.hashtags, r.image_path, r.user_id, u.username, r.city, r.latitude, r.longitude
                    FROM requested_items r
                    JOIN users u ON r.user_id = u.id
                    WHERE r.user_id != ? 
                    AND (r.title LIKE ? OR r.description LIKE ? OR r.hashtags LIKE ?)
                """, (user_id, f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
            else:
                c.execute("""
                    SELECT r.id, r.title, r.description, r.hashtags, r.image_path, r.user_id, u.username, r.city, r.latitude, r.longitude
                    FROM requested_items r
                    JOIN users u ON r.user_id = u.id
                    WHERE r.user_id != ?
                """, (user_id,))
            requested_items = c.fetchall()
            if origin_coords and radius_km > 0:
                lat0, lon0 = origin_coords["lat"], origin_coords["lng"]
                requested_items = [
                    row for row in requested_items
                    if row["latitude"] and row["longitude"] and
                    haversine(lat0, lon0, row["latitude"], row["longitude"]) <= radius_km
                ]

        my_requests = []
        my_items = []
        if user_id_int:
            c.execute("""
                SELECT r.id, r.title, r.description, r.hashtags, r.image_path, r.user_id, u.username, r.city, r.latitude, r.longitude
                FROM requested_items r
                JOIN users u ON r.user_id = u.id
                WHERE r.user_id = ?
            """, (user_id_int,))
            my_requests = c.fetchall()

            c.execute("""
                SELECT i.id, i.name, i.description, i.status, i.hashtags, i.image_path, u.username, i.city, i.latitude, i.longitude
                FROM items i
                JOIN users u ON i.owner_id = u.id
                WHERE i.owner_id = ?
            """, (user_id_int,))
            my_items = c.fetchall()

            c.execute("SELECT username FROM users WHERE id = ?", (user_id_int,))
            row = c.fetchone()
            if row:
                username = row["username"]

    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": user_id_int,
        "username": username,
        "items": items,
        "requested_items": requested_items,
        "my_requests": my_requests,
        "my_items": my_items,
        "tab": tab,
        "cities": CITIES,
        "origin_city": origin_city,
        "radius": radius_km,
    })