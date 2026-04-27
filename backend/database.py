"""
ReadyDay — Database connection
Dev: SQLite (archivo local)
Prod: Supabase (PostgreSQL via supabase-py)

Expone get_db() como dependency de FastAPI.
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import date

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "readyday_dev.db"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
USE_SUPABASE  = bool(SUPABASE_URL and SUPABASE_KEY)


# ─────────────────────────────────────────────
# SQLITE — DEV
# ─────────────────────────────────────────────

def _get_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite():
    """Crea tablas si no existen (dev only)."""
    conn = _get_sqlite()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id     TEXT PRIMARY KEY DEFAULT 'default',
            lang        TEXT NOT NULL DEFAULT 'es',
            goal        TEXT NOT NULL DEFAULT 'health',
            defaults_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS daily_overrides (
            user_id   TEXT NOT NULL DEFAULT 'default',
            date      TEXT NOT NULL,
            override_json TEXT NOT NULL DEFAULT '{}',
            PRIMARY KEY (user_id, date)
        );

        CREATE TABLE IF NOT EXISTS daily_readiness (
            user_id   TEXT NOT NULL DEFAULT 'default',
            date      TEXT NOT NULL,
            data_json TEXT NOT NULL,
            PRIMARY KEY (user_id, date)
        );

        CREATE TABLE IF NOT EXISTS garmin_snapshots (
            user_id     TEXT NOT NULL DEFAULT 'default',
            captured_at TEXT NOT NULL,
            data_json   TEXT NOT NULL,
            PRIMARY KEY (user_id, captured_at)
        );
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# SIMPLE DATA ACCESS LAYER
# Wrappers sincrónicos — suficiente para el MVP.
# Migrar a async SQLAlchemy o supabase-py en Sprint 3.
# ─────────────────────────────────────────────

class Database:
    """Capa de acceso a datos. Soporta SQLite (dev) y Supabase (prod)."""

    def __init__(self):
        if not USE_SUPABASE:
            init_sqlite()

    # ── Preferences ──────────────────────────

    def get_preferences(self, user_id: str = "default") -> dict:
        conn = _get_sqlite()
        row = conn.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)
        ).fetchone()
        conn.close()
        if row:
            prefs = dict(row)
            prefs["defaults"] = json.loads(prefs.pop("defaults_json", "{}"))
            return prefs
        return {"user_id": user_id, "lang": "es", "goal": "health", "defaults": {}}

    def upsert_preferences(self, user_id: str, data: dict):
        conn = _get_sqlite()
        defaults_json = json.dumps(data.get("defaults", {}))
        conn.execute("""
            INSERT INTO user_preferences (user_id, lang, goal, defaults_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                lang = excluded.lang,
                goal = excluded.goal,
                defaults_json = excluded.defaults_json
        """, (user_id, data.get("lang", "es"), data.get("goal", "health"), defaults_json))
        conn.commit()
        conn.close()

    # ── Overrides ────────────────────────────

    def get_override(self, user_id: str = "default", day: str | None = None) -> dict:
        day = day or date.today().isoformat()
        conn = _get_sqlite()
        row = conn.execute(
            "SELECT override_json FROM daily_overrides WHERE user_id = ? AND date = ?",
            (user_id, day)
        ).fetchone()
        conn.close()
        return json.loads(row["override_json"]) if row else {}

    def upsert_override(self, user_id: str, day: str, override: dict):
        conn = _get_sqlite()
        conn.execute("""
            INSERT INTO daily_overrides (user_id, date, override_json)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                override_json = excluded.override_json
        """, (user_id, day, json.dumps(override)))
        conn.commit()
        conn.close()

    # ── Daily Readiness ───────────────────────

    def save_readiness(self, user_id: str, day: str, data: dict):
        conn = _get_sqlite()
        conn.execute("""
            INSERT INTO daily_readiness (user_id, date, data_json)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                data_json = excluded.data_json
        """, (user_id, day, json.dumps(data)))
        conn.commit()
        conn.close()

    def get_readiness(self, user_id: str = "default", day: str | None = None) -> dict | None:
        day = day or date.today().isoformat()
        conn = _get_sqlite()
        row = conn.execute(
            "SELECT data_json FROM daily_readiness WHERE user_id = ? AND date = ?",
            (user_id, day)
        ).fetchone()
        conn.close()
        return json.loads(row["data_json"]) if row else None

    def get_readiness_history(self, user_id: str = "default", days: int = 7) -> list[dict]:
        conn = _get_sqlite()
        rows = conn.execute("""
            SELECT data_json FROM daily_readiness
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT ?
        """, (user_id, days)).fetchall()
        conn.close()
        return [json.loads(r["data_json"]) for r in rows]

    # ── Garmin Snapshots ──────────────────────

    def save_snapshot(self, user_id: str, snapshot: dict):
        conn = _get_sqlite()
        conn.execute("""
            INSERT INTO garmin_snapshots (user_id, captured_at, data_json)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, captured_at) DO UPDATE SET
                data_json = excluded.data_json
        """, (user_id, snapshot.get("capturedAt", ""), json.dumps(snapshot)))
        conn.commit()
        conn.close()

    def get_latest_snapshot(self, user_id: str = "default") -> dict | None:
        conn = _get_sqlite()
        row = conn.execute("""
            SELECT data_json FROM garmin_snapshots
            WHERE user_id = ?
            ORDER BY captured_at DESC
            LIMIT 1
        """, (user_id,)).fetchone()
        conn.close()
        return json.loads(row["data_json"]) if row else None


# Singleton — una instancia compartida por todos los routers
db = Database()
