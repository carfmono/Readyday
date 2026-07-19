from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid
import enum


def new_uuid() -> str:
    return str(uuid.uuid4())


class WearableSource(str, enum.Enum):
    garmin = "garmin"
    apple_watch = "apple_watch"
    fitbit = "fitbit"
    samsung = "samsung"
    manual = "manual"


class Zone(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    lang = Column(String, default="es")
    goal = Column(String, default="health")  # health | performance | longevity
    timezone = Column(String, default="America/Bogota")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    snapshots = relationship("DeviceSnapshot", back_populates="user")
    scores = relationship("DailyScore", back_populates="user")
    devices = relationship("UserDevice", back_populates="user")
    push_tokens = relationship("PushToken", back_populates="user")


class UserDevice(Base):
    """Credenciales y configuración por wearable por usuario."""
    __tablename__ = "user_devices"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    source = Column(String, nullable=False)  # garmin | apple_watch | etc.
    # Credenciales encriptadas (Fernet) — solo para pull desde cloud
    encrypted_credentials = Column(Text, nullable=True)
    is_connected = Column(Boolean, default=False)
    connected_at = Column(DateTime, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="devices")


class DeviceSnapshot(Base):
    """Datos crudos recibidos desde cualquier wearable."""
    __tablename__ = "device_snapshots"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    source = Column(String, nullable=False)  # WearableSource
    captured_at = Column(DateTime, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)

    # Métricas normalizadas (todas las fuentes mapean a estos campos)
    body_battery = Column(Float, nullable=True)      # 0-100
    sleep_score = Column(Float, nullable=True)       # 0-100
    sleep_hours = Column(Float, nullable=True)       # horas decimales
    hr_resting = Column(Float, nullable=True)        # bpm
    stress_avg = Column(Float, nullable=True)        # 0-100
    activity_load = Column(Float, nullable=True)     # 0-100 (proxy)
    recovery_time_h = Column(Float, nullable=True)   # horas

    # Payload original del dispositivo (JSON como texto)
    raw_payload = Column(Text, nullable=True)

    user = relationship("User", back_populates="snapshots")
    daily_score = relationship("DailyScore", back_populates="snapshot", uselist=False)


class DailyScore(Base):
    """Score calculado por día por usuario."""
    __tablename__ = "daily_scores"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    snapshot_id = Column(String, ForeignKey("device_snapshots.id"), nullable=True)
    date = Column(String, nullable=False)  # ISO date "2026-07-19"
    computed_at = Column(DateTime, default=datetime.utcnow)

    # Scores
    recovery_score = Column(Integer, nullable=False)   # 0-100
    strain_score = Column(Integer, nullable=False)     # 0-100
    balance_score = Column(Float, nullable=False)      # puede ser negativo
    zone = Column(String, nullable=False)              # green|yellow|red
    confidence = Column(Integer, nullable=True)        # 0-100 (datos disponibles)

    # Hábitos usados en el cálculo
    caffeine_cups = Column(Integer, default=0)
    alcohol_drinks = Column(Integer, default=0)
    late_dinner = Column(Boolean, default=False)
    energy_manual = Column(Integer, nullable=True)     # 0-4 override manual

    # Textos generados (Claude o plantillas)
    recommendation = Column(Text, nullable=True)
    insight = Column(Text, nullable=True)
    top_factors = Column(Text, nullable=True)          # JSON list como texto

    # Notificación push enviada
    push_sent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="scores")
    snapshot = relationship("DeviceSnapshot", back_populates="daily_score")


class PushToken(Base):
    """Tokens FCM por usuario para notificaciones Android."""
    __tablename__ = "push_tokens"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    platform = Column(String, nullable=False)  # android | ios
    token = Column(String, nullable=False, unique=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="push_tokens")
