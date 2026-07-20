"""
Garmin router — conexión de cuenta y sync inmediato desde el dashboard.
"""
import json
import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import DailyScore, DeviceSnapshot, User, UserDevice
from services.garmin_service import (
    decrypt_credentials,
    encrypt_credentials,
    fetch_snapshot,
)
from services.score_engine import compute_daily_readiness
from services.explanation_engine import generate_explanation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/garmin", tags=["garmin"])


class GarminConnectBody(BaseModel):
    garmin_email: str
    garmin_password: str


@router.get("/status")
def garmin_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = db.query(UserDevice).filter(
        UserDevice.user_id == current_user.id,
        UserDevice.source == "garmin",
    ).first()
    return {
        "connected": device is not None and device.is_connected,
        "has_credentials": device is not None and device.encrypted_credentials is not None,
        "connected_at": device.connected_at.isoformat() if device and device.connected_at else None,
    }


@router.post("/connect")
def connect_garmin(
    body: GarminConnectBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not body.garmin_email.strip() or not body.garmin_password:
        raise HTTPException(status_code=400, detail="Email y contraseña de Garmin requeridos")

    encrypted = encrypt_credentials(body.garmin_email.strip(), body.garmin_password)
    if not encrypted:
        raise HTTPException(
            status_code=500,
            detail="No se pudo encriptar. Verifica que ENCRYPTION_KEY esté configurada en el servidor.",
        )

    device = db.query(UserDevice).filter(
        UserDevice.user_id == current_user.id,
        UserDevice.source == "garmin",
    ).first()

    if device:
        device.is_connected = True
        device.connected_at = datetime.now(timezone.utc)
        device.encrypted_credentials = encrypted
    else:
        device = UserDevice(
            user_id=current_user.id,
            source="garmin",
            is_connected=True,
            connected_at=datetime.now(timezone.utc),
            encrypted_credentials=encrypted,
        )
        db.add(device)

    db.commit()
    return {"ok": True, "message": "Cuenta Garmin conectada"}


@router.post("/sync-now")
async def sync_now(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pull inmediato de datos Garmin para el usuario actual → calcula score del día."""
    device = db.query(UserDevice).filter(
        UserDevice.user_id == current_user.id,
        UserDevice.source == "garmin",
        UserDevice.is_connected == True,
        UserDevice.encrypted_credentials.isnot(None),
    ).first()

    if not device:
        raise HTTPException(
            status_code=400,
            detail="Garmin no conectado. Ingresa tus credenciales primero.",
        )

    creds = decrypt_credentials(device.encrypted_credentials)
    if not creds:
        raise HTTPException(status_code=500, detail="Error descifrando credenciales.")

    try:
        snap_data = await fetch_snapshot(current_user.id, creds[0], creds[1])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error conectando con Garmin: {e}")

    snap = DeviceSnapshot(
        user_id=current_user.id,
        source="garmin",
        captured_at=datetime.now(timezone.utc),
        body_battery=snap_data.get("body_battery"),
        sleep_score=snap_data.get("sleep_score"),
        sleep_hours=snap_data.get("sleep_hours"),
        hr_resting=snap_data.get("hr_resting"),
        stress_avg=snap_data.get("stress_avg"),
        activity_load=snap_data.get("activity_load"),
        recovery_time_h=snap_data.get("recovery_time_h"),
    )
    db.add(snap)
    db.flush()

    from routers.snapshots import _snapshot_to_dict
    result = compute_daily_readiness(_snapshot_to_dict(snap))
    texts = await generate_explanation(result["zone"], result["top_factors"], result, current_user.lang)

    today = date.today().isoformat()
    existing = db.query(DailyScore).filter(
        DailyScore.user_id == current_user.id,
        DailyScore.date == today,
    ).first()

    if existing:
        existing.snapshot_id = snap.id
        existing.recovery_score = result["recovery_score"]
        existing.strain_score = result["strain_score"]
        existing.balance_score = result["balance_score"]
        existing.zone = result["zone"]
        existing.confidence = result["confidence"]
        existing.recommendation = texts.get("recommendation")
        existing.insight = texts.get("insight")
        existing.top_factors = json.dumps(result["top_factors"])
    else:
        existing = DailyScore(
            user_id=current_user.id,
            date=today,
            snapshot_id=snap.id,
            recovery_score=result["recovery_score"],
            strain_score=result["strain_score"],
            balance_score=result["balance_score"],
            zone=result["zone"],
            confidence=result["confidence"],
            recommendation=texts.get("recommendation"),
            insight=texts.get("insight"),
            top_factors=json.dumps(result["top_factors"]),
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)

    return {
        "ok": True,
        "zone": existing.zone,
        "recovery_score": existing.recovery_score,
        "message": f"Sincronizado — zona {existing.zone}",
        "raw": snap_data,
    }
