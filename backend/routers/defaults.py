"""
ReadyDay — /defaults router
GET  /defaults   → devuelve HabitDefaults del usuario
PATCH /defaults  → actualiza defaults (merge parcial)
"""

from fastapi import APIRouter
from models import DefaultsPatchRequest
from database import db

router = APIRouter(prefix="/defaults", tags=["defaults"])


@router.get("")
def get_defaults():
    """Devuelve los HabitDefaults persistidos del usuario."""
    user_id = "default"
    prefs = db.get_preferences(user_id)
    defaults = prefs.get("defaults", {})

    # Normaliza estructura esperada si no existe
    canonical = {
        "caffeineLate": {"cups": 0, "lastTime": None},
        "alcohol":      {"drinks": 0},
        "lateDinner":   {"ate": False, "time": None},
    }
    for k, v in canonical.items():
        if k not in defaults:
            defaults[k] = v

    return {"data": defaults, "error": None}


@router.patch("")
def patch_defaults(body: DefaultsPatchRequest):
    """
    Actualiza los HabitDefaults. Solo los campos enviados se sobreescriben.
    Los campos no enviados quedan igual.
    """
    user_id = "default"
    prefs = db.get_preferences(user_id)
    current = prefs.get("defaults", {})

    patch = body.model_dump(exclude_none=True)
    merged = {**current, **patch}

    prefs["defaults"] = merged
    db.upsert_preferences(user_id, prefs)

    return {"data": merged, "error": None}
