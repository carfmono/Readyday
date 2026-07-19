from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, PushToken
from schemas import RegisterPushTokenRequest, MessageOut
from auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("/register", response_model=MessageOut, status_code=201)
def register_token(
    body: RegisterPushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra o actualiza el FCM token del dispositivo del usuario."""
    existing = db.query(PushToken).filter(PushToken.token == body.token).first()

    if existing:
        existing.user_id = current_user.id
        existing.platform = body.platform
        existing.last_used_at = datetime.utcnow()
        existing.is_active = True
    else:
        # Desactivar tokens previos del mismo usuario en esta plataforma
        db.query(PushToken).filter(
            PushToken.user_id == current_user.id,
            PushToken.platform == body.platform,
        ).update({"is_active": False})

        token = PushToken(
            user_id=current_user.id,
            platform=body.platform,
            token=body.token,
        )
        db.add(token)

    db.commit()
    return MessageOut(message="Token registrado")


@router.delete("/unregister", response_model=MessageOut)
def unregister_token(
    body: RegisterPushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(PushToken).filter(
        PushToken.user_id == current_user.id,
        PushToken.token == body.token,
    ).update({"is_active": False})
    db.commit()
    return MessageOut(message="Token desregistrado")
