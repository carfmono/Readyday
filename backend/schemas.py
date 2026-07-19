from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    lang: Literal["es", "en"] = "es"
    goal: Literal["health", "performance", "longevity"] = "health"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    lang: str
    goal: str
    timezone: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Device Snapshot (entrada multi-wearable) ─────────────────────────────────

WearableSource = Literal["garmin", "apple_watch", "fitbit", "samsung", "manual"]

class SnapshotIn(BaseModel):
    source: WearableSource
    captured_at: datetime
    body_battery: Optional[float] = Field(None, ge=0, le=100)
    sleep_score: Optional[float] = Field(None, ge=0, le=100)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    hr_resting: Optional[float] = Field(None, ge=20, le=250)
    stress_avg: Optional[float] = Field(None, ge=0, le=100)
    activity_load: Optional[float] = Field(None, ge=0, le=100)
    recovery_time_h: Optional[float] = Field(None, ge=0, le=96)

    # Hábitos del día (opcionales, mejoran el cálculo)
    caffeine_cups: int = 0
    alcohol_drinks: int = 0
    late_dinner: bool = False
    energy_manual: Optional[int] = Field(None, ge=0, le=4)

    # Payload original del dispositivo (para auditoría)
    raw_payload: Optional[dict] = None


class SnapshotOut(BaseModel):
    snapshot_id: str
    score: "ScoreOut"


# ── Scores ───────────────────────────────────────────────────────────────────

class ScoreOut(BaseModel):
    id: str
    date: str
    recovery_score: int
    strain_score: int
    balance_score: float
    zone: str
    confidence: Optional[int]
    recommendation: Optional[str]
    insight: Optional[str]
    top_factors: Optional[list[str]]

    # Input snapshot (para display)
    body_battery: Optional[float] = None
    sleep_score: Optional[float] = None
    sleep_hours: Optional[float] = None
    hr_resting: Optional[float] = None
    stress_avg: Optional[float] = None
    activity_load: Optional[float] = None
    recovery_time_h: Optional[float] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


class ScoreHistoryOut(BaseModel):
    scores: list[ScoreOut]
    days: int


# ── Device connection ─────────────────────────────────────────────────────────

class ConnectDeviceRequest(BaseModel):
    source: WearableSource
    garmin_email: Optional[str] = None
    garmin_password: Optional[str] = None


class DeviceStatusOut(BaseModel):
    source: str
    is_connected: bool
    last_sync_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Push Notifications ────────────────────────────────────────────────────────

class RegisterPushTokenRequest(BaseModel):
    platform: Literal["android", "ios"]
    token: str


# ── Habits Override ───────────────────────────────────────────────────────────

class HabitOverrideRequest(BaseModel):
    caffeine_cups: int = Field(0, ge=0, le=20)
    alcohol_drinks: int = Field(0, ge=0, le=20)
    late_dinner: bool = False
    energy_manual: Optional[int] = Field(None, ge=0, le=4)


# ── Generic response ──────────────────────────────────────────────────────────

class MessageOut(BaseModel):
    message: str
    detail: Optional[str] = None
