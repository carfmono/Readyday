from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserDevice
from schemas import ConnectDeviceRequest, DeviceStatusOut, MessageOut
from auth import get_current_user
from services.garmin_service import encrypt_credentials

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceStatusOut])
def list_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(UserDevice).filter(UserDevice.user_id == current_user.id).all()


@router.post("/connect", response_model=DeviceStatusOut, status_code=201)
def connect_device(
    body: ConnectDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Conecta un wearable al usuario.
    Para Garmin: guarda credenciales encriptadas para el pull nocturno.
    Para Connect IQ / Apple Watch: solo registra el device como conectado (los datos llegan via app).
    """
    device = db.query(UserDevice).filter(
        UserDevice.user_id == current_user.id,
        UserDevice.source == body.source,
    ).first()

    encrypted = None
    if body.source == "garmin" and body.garmin_email and body.garmin_password:
        encrypted = encrypt_credentials(body.garmin_email, body.garmin_password)
        if not encrypted:
            raise HTTPException(status_code=500, detail="No se pudo encriptar las credenciales. Configura ENCRYPTION_KEY.")

    if device:
        device.is_connected = True
        device.connected_at = datetime.utcnow()
        if encrypted:
            device.encrypted_credentials = encrypted
    else:
        device = UserDevice(
            user_id=current_user.id,
            source=body.source,
            is_connected=True,
            connected_at=datetime.utcnow(),
            encrypted_credentials=encrypted,
        )
        db.add(device)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/{source}", response_model=MessageOut)
def disconnect_device(
    source: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = db.query(UserDevice).filter(
        UserDevice.user_id == current_user.id,
        UserDevice.source == source,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no conectado")

    device.is_connected = False
    device.encrypted_credentials = None
    db.commit()
    return MessageOut(message=f"{source} desconectado")
