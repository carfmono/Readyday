from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut, MessageOut
from auth import hash_password, verify_password, create_access_token, get_current_user
from config import get_settings
from jose import jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        lang=body.lang,
        goal=body.goal,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user_id=user.id, name=user.name)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user_id=user.id, name=user.name)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/device-token", summary="Token de larga duración para dispositivos (reloj Garmin CIQ)")
def device_token(current_user: User = Depends(get_current_user)):
    """
    Genera un JWT de 1 año para usar en dispositivos wearable (Garmin CIQ, etc.).
    Cópialo en los ajustes del widget del reloj.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=365)
    token = jwt.encode(
        {"sub": current_user.id, "email": current_user.email, "exp": expire, "type": "device"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return {
        "device_token": token,
        "expires_in_days": 365,
        "instructions": "Copia este token en los ajustes del widget ReadyDay de tu reloj Garmin.",
    }


@router.delete("/me", response_model=MessageOut)
def deactivate(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.is_active = False
    db.commit()
    return MessageOut(message="Cuenta desactivada")
