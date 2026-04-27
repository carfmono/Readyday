"""
ReadyDay — /overrides router
GET /overrides/today  → devuelve HabitOverride de hoy
PUT /overrides/today  → guarda/reemplaza override del día
"""

from datetime import date
from fastapi import APIRouter, Query
from models import OverridePutRequest
from database import db

router = APIRouter(prefix="/overrides", tags=["overrides"])


@router.get("/today")
def get_today_override(day: str = Query(None, description="ISO date, default = today")):
    """Devuelve el HabitOverride guardado para el día indicado (default: hoy)."""
    user_id = "default"
    target_day = day or date.today().isoformat()
    override = db.get_override(user_id, target_day)
    return {"data": override, "error": None}


@router.put("/today")
def put_today_override(body: OverridePutRequest, day: str = Query(None)):
    """
    Guarda el HabitOverride del día.
    PUT reemplaza el override completo (no merge parcial).
    Usa PATCH /defaults para cambios permanentes.
    """
    user_id = "default"
    target_day = day or date.today().isoformat()
    override_data = body.model_dump(exclude_none=True)
    db.upsert_override(user_id, target_day, override_data)
    return {"data": override_data, "error": None}
