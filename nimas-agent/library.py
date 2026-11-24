"""Small local SQLite catalog for NIMAS projects."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

def connect(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT NOT NULL, path TEXT NOT NULL UNIQUE, mode TEXT NOT NULL, status TEXT NOT NULL, cover TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
    db.commit()
    return db

def register(db_path: Path, name: str, project_path: Path, mode="pdf_only", status="intake_complete", cover=None):
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as db:
        db.execute("INSERT INTO projects(name,path,mode,status,cover,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET name=excluded.name, mode=excluded.mode, status=excluded.status, cover=excluded.cover, updated_at=excluded.updated_at", (name, str(project_path), mode, status, cover, now, now))
        db.commit()

def all_projects(db_path: Path):
    with connect(db_path) as db:
        return [dict(row) for row in db.execute("SELECT * FROM projects ORDER BY updated_at DESC")]
