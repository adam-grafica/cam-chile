"""
CAM-CHILE - Backend FastAPI
Orquestador principal para descubrimiento y visualización de cámaras en tiempo real
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import sqlite3
import asyncio

app = FastAPI(title="CAM-CHILE API", version="1.0.0")

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB SQLite
DB_PATH = "db/cameras.db"

def init_db():
    """Inicializa la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            lat REAL,
            lon REAL,
            feed_type TEXT,
            stream_url TEXT,
            address TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Endpoints
@app.get("/")
def root():
    return {"status": "online", "project": "CAM-CHILE"}

@app.get("/api/cameras")
def get_cameras() -> List[Dict]:
    """Obtiene todas las cámaras"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cameras")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "name": r[1],
            "lat": r[2],
            "lon": r[3],
            "feed_type": r[4],
            "stream_url": r[5],
            "address": r[6],
            "last_updated": r[7]
        }
        for r in rows
    ]

@app.post("/api/cameras")
def add_camera(camera: Dict):
    """Agrega una nueva cámara"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO cameras (name, lat, lon, feed_type, stream_url, address)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            camera["name"],
            camera.get("lat"),
            camera.get("lon"),
            camera.get("feed_type"),
            camera.get("stream_url"),
            camera.get("address")
        )
    )
    conn.commit()
    conn.close()
    return {"status": "created", "id": cursor.lastrowid}

@app.get("/api/agents/jobs")
def get_agent_jobs():
    """Estado de los agentes (placeholder)"""
    return {
        "scraper": "idle",
        "osint": "idle",
        "rtsp_bridge": "idle"
    }

# Inicializar DB al startup
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
