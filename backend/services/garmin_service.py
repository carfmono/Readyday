"""
Garmin Service — pull de datos desde Garmin Connect cloud (modo polling).
Para la integración "bien hecha" (Connect IQ), el watch envía los datos directamente
via la app Android. Este servicio es el fallback para usuarios sin Connect IQ o para
el sync nocturno cuando el reloj sincronizó pero el usuario no abrió la app.
"""

import logging
import os
from datetime import date, datetime
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_fernet() -> Optional[Fernet]:
    key = settings.encryption_key
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        return None


def encrypt_credentials(email: str, password: str) -> Optional[str]:
    """Retorna credenciales encriptadas como string. None si no hay clave de encriptación."""
    f = _get_fernet()
    if not f:
        return None
    import json
    payload = json.dumps({"email": email, "password": password}).encode()
    return f.encrypt(payload).decode()


def decrypt_credentials(encrypted: str) -> Optional[tuple[str, str]]:
    """Retorna (email, password) o None si falla la desencriptación."""
    f = _get_fernet()
    if not f:
        return None
    try:
        import json
        data = json.loads(f.decrypt(encrypted.encode()).decode())
        return data["email"], data["password"]
    except (InvalidToken, KeyError, Exception):
        return None


class GarminSession:
    """Sesión Garmin por usuario con auto-renovación."""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._client = None
        self._logged_in_at: Optional[datetime] = None

    def _needs_refresh(self) -> bool:
        if self._client is None or self._logged_in_at is None:
            return True
        # Renovar si la sesión tiene más de 50 minutos
        age = (datetime.utcnow() - self._logged_in_at).total_seconds()
        return age > 3000

    def get_client(self):
        if self._needs_refresh():
            try:
                from garminconnect import Garmin
                client = Garmin(self.email, self.password)
                client.login()
                self._client = client
                self._logged_in_at = datetime.utcnow()
                logger.info("Garmin Connect: sesión renovada para %s", self.email)
            except Exception as e:
                logger.error("Garmin login failed: %s", e)
                raise
        return self._client


# Cache de sesiones por user_id
_sessions: dict[str, GarminSession] = {}


def get_session(user_id: str, email: str, password: str) -> GarminSession:
    if user_id not in _sessions:
        _sessions[user_id] = GarminSession(email, password)
    return _sessions[user_id]


def clear_session(user_id: str):
    _sessions.pop(user_id, None)


async def fetch_snapshot(user_id: str, email: str, password: str, target_date: Optional[date] = None) -> dict:
    """
    Pull de snapshot Garmin para una fecha.
    Retorna dict con campos normalizados (misma forma que SnapshotIn).
    """
    if target_date is None:
        target_date = date.today()

    day_str = target_date.isoformat()
    session = get_session(user_id, email, password)
    client = session.get_client()
    snap: dict = {"source": "garmin", "captured_at": f"{day_str}T06:00:00Z"}

    # Body Battery
    try:
        bb_data = client.get_body_battery(day_str)
        if bb_data:
            vals = [r.get("value") for r in bb_data if r.get("value") is not None]
            snap["body_battery"] = float(max(vals)) if vals else None
        else:
            snap["body_battery"] = None
    except Exception as e:
        logger.warning("bodyBattery: %s", e)
        snap["body_battery"] = None

    # Sleep
    try:
        sleep_data = client.get_sleep_data(day_str)
        daily = (sleep_data or {}).get("dailySleepDTO", {})
        raw_score = daily.get("sleepScores", {})
        snap["sleep_score"] = raw_score.get("overall", {}).get("value") if isinstance(raw_score, dict) else None
        dur_s = daily.get("sleepTimeSeconds")
        snap["sleep_hours"] = round(dur_s / 3600, 2) if dur_s else None
    except Exception as e:
        logger.warning("sleep: %s", e)
        snap["sleep_score"] = snap["sleep_hours"] = None

    # Resting HR
    try:
        hr_data = client.get_rhr_day(day_str)
        if hr_data:
            vals = hr_data.get("allMetrics", {}).get("metricsMap", {}).get("WELLNESS_RESTING_HEART_RATE", [])
            snap["hr_resting"] = float(vals[0]["value"]) if vals else None
        else:
            snap["hr_resting"] = None
    except Exception as e:
        logger.warning("hr_resting: %s", e)
        snap["hr_resting"] = None

    # Stress
    try:
        stress = client.get_stress_data(day_str)
        avg = (stress or {}).get("avgStressLevel")
        snap["stress_avg"] = float(avg) if avg and avg > 0 else None
    except Exception as e:
        logger.warning("stress: %s", e)
        snap["stress_avg"] = None

    # Activity Load (proxy: min moderados + 2×min vigorosos, normalizado a 100)
    try:
        stats = client.get_stats(day_str)
        mod = stats.get("moderateIntensityMinutes", 0) or 0
        vig = stats.get("vigorousIntensityMinutes", 0) or 0
        total_min = mod + vig * 2
        snap["activity_load"] = min(100.0, round(total_min / 1.2, 1)) if total_min > 0 else 0.0
    except Exception as e:
        logger.warning("activity_load: %s", e)
        snap["activity_load"] = None

    # Recovery Time (desde HRV)
    try:
        hrv = client.get_hrv_data(day_str)
        rt = (hrv or {}).get("hrvSummary", {}).get("recoveryTime")
        snap["recovery_time_h"] = float(rt) if rt else None
    except Exception as e:
        logger.warning("recovery_time_h: %s", e)
        snap["recovery_time_h"] = None

    logger.info("Garmin snapshot %s para user %s: %s", day_str, user_id, snap)
    return snap
