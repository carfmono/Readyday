"""
ReadyDay — Snapshot Normalizer
Capa de limpieza previa al score engine.
Convierte datos crudos de Garmin en un CleanSnapshot validado.
Funciones puras — sin efectos secundarios.
"""

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

# Defaults razonables cuando el dato no está disponible en Garmin
DEFAULTS: dict[str, float] = {
    "bodyBattery":   50.0,
    "sleepScore":    50.0,
    "sleepHours":    7.0,
    "hrResting":     65.0,
    "stressAvg":     50.0,
    "activityLoad":  0.0,
    "recoveryTimeH": 0.0,
}

# Rangos fisiológicos válidos (min, max)
RANGES: dict[str, tuple[float, float]] = {
    "bodyBattery":   (0.0,   100.0),
    "sleepScore":    (0.0,   100.0),
    "sleepHours":    (0.0,    24.0),
    "hrResting":     (30.0,  220.0),
    "stressAvg":     (0.0,   100.0),
    "activityLoad":  (0.0,   100.0),
    "recoveryTimeH": (0.0,  168.0),   # máx 1 semana
}

# Métricas clave → ausencia impacta mucho el confidence score
KEY_METRICS: list[str] = ["bodyBattery", "sleepScore", "hrResting"]

# Métricas secundarias → ausencia impacta menos
SECONDARY_METRICS: list[str] = ["sleepHours", "stressAvg", "activityLoad", "recoveryTimeH"]

ALL_METRICS: list[str] = KEY_METRICS + SECONDARY_METRICS


# ─────────────────────────────────────────────
# NORMALIZACIÓN
# ─────────────────────────────────────────────

def normalize_snapshot(raw: dict) -> dict:
    """
    Convierte un GarminSnapshot crudo en un CleanSnapshot normalizado.

    Pasos:
    1. Valores None → default razonable
    2. Valores fuera de rango → clampeo a límite
    3. Todo convertido a float
    4. Incluye metadatos de campos nulos para el confidence score

    Retorna el mismo shape que GarminSnapshot con todos los campos siempre presentes.
    """
    null_fields: list[str] = []
    clean: dict = {"capturedAt": raw.get("capturedAt", "")}

    for key in ALL_METRICS:
        raw_val = raw.get(key)

        if raw_val is None:
            clean[key] = DEFAULTS[key]
            null_fields.append(key)
        else:
            try:
                v = float(raw_val)
                lo, hi = RANGES[key]
                clean[key] = max(lo, min(hi, v))
            except (TypeError, ValueError):
                clean[key] = DEFAULTS[key]
                null_fields.append(key)

    # Metadatos internos — no se exponen en la API, útiles para logging
    clean["_nullFields"] = null_fields
    return clean


def calculate_confidence(raw: dict) -> int:
    """
    Calcula qué tan confiables son los datos de entrada (0-100).

    Escala:
    - Todas las métricas presentes              → 95
    - Falta 1 métrica secundaria                → 80
    - Faltan 2 métricas secundarias             → 70
    - Faltan 3+ métricas secundarias            → 60
    - Falta 1 métrica clave                     → 55
    - Faltan 2 métricas clave                   → 35
    - Faltan todas las claves                   → 20
    """
    missing_key = sum(1 for m in KEY_METRICS      if raw.get(m) is None)
    missing_sec = sum(1 for m in SECONDARY_METRICS if raw.get(m) is None)

    if missing_key == 0 and missing_sec == 0: return 95
    if missing_key == 0 and missing_sec == 1: return 80
    if missing_key == 0 and missing_sec == 2: return 70
    if missing_key == 0:                      return 60
    if missing_key == 1:                      return 55
    if missing_key == 2:                      return 35
    return 20


def get_null_fields(raw: dict) -> list[str]:
    """Devuelve los nombres de los campos que vinieron null en el snapshot."""
    return [m for m in ALL_METRICS if raw.get(m) is None]


# ─────────────────────────────────────────────
# NORMALIZACIÓN DE HÁBITOS
# ─────────────────────────────────────────────

def normalize_habits(raw_habits: dict | None) -> dict:
    """
    Normaliza el dict de hábitos asegurando estructura completa y tipos correctos.
    Acepta tanto la forma dict expandida como la forma booleana legacy.
    """
    h = raw_habits or {}

    # caffeineLate
    caffeine = h.get("caffeineLate", {})
    if not isinstance(caffeine, dict):
        caffeine = {"cups": 2 if caffeine else 0, "lastTime": None}
    caffeine_clean = {
        "cups":     int(caffeine.get("cups") or 0),
        "lastTime": caffeine.get("lastTime"),
    }

    # alcohol
    alcohol = h.get("alcohol", {})
    if not isinstance(alcohol, dict):
        alcohol = {"drinks": 2 if alcohol else 0}
    alcohol_clean = {
        "drinks": int(alcohol.get("drinks") or 0),
    }

    # lateDinner
    dinner = h.get("lateDinner", {})
    if not isinstance(dinner, dict):
        dinner = {"ate": bool(dinner), "time": "22:00"}
    dinner_clean = {
        "ate":  bool(dinner.get("ate") or False),
        "time": dinner.get("time"),
    }

    return {
        "caffeineLate":  caffeine_clean,
        "alcohol":       alcohol_clean,
        "lateDinner":    dinner_clean,
        "energyManual":  h.get("energyManual"),
    }
