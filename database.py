import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos de ofertas laborales si no existe."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                url TEXT NOT NULL,
                published_time TEXT,
                notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source ON jobs(source);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notified_at ON jobs(notified_at);
        ''')
        conn.commit()

def generate_job_id(source: str, url: str, title: str, company: str) -> str:
    """Genera un identificador único y determinista para evitar duplicados."""
    # Si la URL tiene un id limpio, usarlo; o crear hash del conjunto
    clean_url = url.split("?")[0].strip().lower()
    raw = f"{source}:{clean_url}:{title.strip().lower()}:{company.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

def is_job_seen(job_id: str) -> bool:
    """Verifica si la vacante ya fue guardada y notificada previamente."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,))
        return cursor.fetchone() is not None

def save_job(job: dict) -> bool:
    """
    Guarda una vacante si no existe.
    Retorna True si fue insertada (es nueva), False si ya existía.
    """
    job_id = job.get("id") or generate_job_id(
        job.get("source", ""),
        job.get("url", ""),
        job.get("title", ""),
        job.get("company", "")
    )
    job["id"] = job_id
    
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO jobs (id, source, title, company, location, url, published_time, notified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                job.get("source", "Desconocido"),
                job.get("title", "Sin título"),
                job.get("company", "Confidencial"),
                job.get("location", "Costa Rica"),
                job.get("url", ""),
                job.get("published_time", "Reciente"),
                datetime.now().isoformat()
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def get_stats() -> dict:
    """Retorna métricas del historial de vacantes detectadas."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM jobs")
        total = cursor.fetchone()["total"]
        
        cursor.execute("SELECT source, COUNT(*) as count FROM jobs GROUP BY source")
        by_source = {row["source"]: row["count"] for row in cursor.fetchall()}
        
        cursor.execute("SELECT * FROM jobs ORDER BY notified_at DESC LIMIT 5")
        recent = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_jobs": total,
            "by_source": by_source,
            "recent_samples": recent
        }

