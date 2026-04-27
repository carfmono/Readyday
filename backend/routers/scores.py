"""
ReadyDay — /scores router
Orquesta el pipeline completo:
  normalize → score → explain → recommend → log → persist

GET  /scores/today           → DailyReadiness del día actual
GET  /scores/history         → últimos N días persistidos
POST /scores/compute         → cálculo on-the-fly (no persiste)
POST /scores/snapshot        → ingesta snapshot de Garmin
"""

from datetime import date, datetime, timezone
from fastapi import APIRouter, Query

from normalize_snapshot import normalize_snapshot, calculate_confidence, get_null_fields, normalize_habits
from score_engine import compute_daily_readiness
from explanation_engine import explain
from recommendation_engine import get_recommendation
from logging_utils import log_decision, log_snapshot_ingested
from feature_flags import flags
from models import ComputeRequest, GarminSnapshot
from database import db

router = APIRouter(prefix="/scores", tags=["scores"])


# ── Mock snapshot para dev cuando no hay datos Garmin reales ─────────────────
_MOCK_SNAPSHOT_RAW = {
    "capturedAt":    datetime.now(timezone.utc).isoformat(),
    "bodyBattery":   67,
    "stressAvg":     45,
    "hrResting":     59,
    "sleepScore":    74,
    "sleepHours":    7.2,
    "activityLoad":  40,
    "recoveryTimeH": 28,
}


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def _run_pipeline(
    raw_snapshot: dict,
    raw_habits: dict,
    lang: str,
    day: str,
) -> dict:
    """
    Pipeline completo ReadyDay:
    1. normalize_snapshot   → limpieza + defaults
    2. calculate_confidence → qué tan completos son los datos
    3. compute_daily_readiness → scores matemáticos
    4. explanation_engine.explain → topFactors + insight + prediction + factorExplanations
    5. recommendation_engine → decisión corta
    """

    # 1. Normalización
    clean   = normalize_snapshot(raw_snapshot)
    habits  = normalize_habits(raw_habits)
    missing = get_null_fields(raw_snapshot)

    # 2. Confidence
    confidence = calculate_confidence(raw_snapshot) if flags.CONFIDENCE_SCORE else 100

    # 3. Score engine (matemática pura)
    scores = compute_daily_readiness(clean, habits)
    zone   = scores["zone"]

    # 4. Explanation engine (topFactors + insight + prediction + factorExplanations)
    explanations = explain(
        zone,
        clean,
        habits,
        lang,                                           # type: ignore[arg-type]
        include_explanations=flags.FACTOR_EXPLANATIONS,
    )

    # 5. Recommendation engine (decisión corta)
    recommendation = get_recommendation(zone, clean, lang)  # type: ignore[arg-type]

    # Componer respuesta
    readiness: dict = {
        "date":            day,
        **scores,
        "confidenceScore": confidence if flags.CONFIDENCE_SCORE else None,
        "recommendation":  recommendation,
        "insight":         explanations["insight"],
        "topFactors":      explanations["topFactors"],
        "defaultsUsed":    habits,
        "overridesToday":  {},
    }

    # Prediction solo si el flag está activo
    if flags.PREDICTION:
        readiness["prediction"] = explanations["prediction"]

    # Factor explanations solo si el flag está activo
    if flags.FACTOR_EXPLANATIONS:
        readiness["factorExplanations"] = explanations.get("factorExplanations", [])

    # Strip campos internos del snapshot normalizado
    readiness.pop("_nullFields", None)

    # Log estructurado
    log_decision(clean, readiness, confidence, missing)

    return readiness


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.get("/today")
def get_today(lang: str = Query("es", pattern="^(es|en)$")):
    """
    Devuelve el DailyReadiness del día actual.
    Usa el snapshot más reciente de Garmin (o mock si no hay datos).
    Aplica los overrides del usuario para hoy.
    """
    user_id = "default"
    today   = date.today().isoformat()

    # Snapshot más reciente (real o mock)
    raw_snapshot = db.get_latest_snapshot(user_id) or _MOCK_SNAPSHOT_RAW

    # Defaults + overrides
    prefs        = db.get_preferences(user_id)
    raw_defaults = prefs.get("defaults", {})
    raw_override = db.get_override(user_id, today)
    raw_habits   = {**raw_defaults, **raw_override}
    lang_used    = lang or prefs.get("lang", "es")

    readiness = _run_pipeline(raw_snapshot, raw_habits, lang_used, today)

    if flags.AUTO_PERSIST:
        db.save_readiness(user_id, today, readiness)

    return {"data": readiness, "error": None}


@router.get("/history")
def get_history(days: int = Query(7, ge=1, le=90)):
    """
    Devuelve los últimos `days` días de DailyReadiness calculados y persistidos.
    """
    user_id = "default"
    history = db.get_readiness_history(user_id, days)
    return {"data": history, "error": None}


@router.post("/compute")
def compute_on_the_fly(body: ComputeRequest):
    """
    Calcula DailyReadiness on-the-fly desde snapshot enviado en el body.
    Útil para el Garmin bridge y para tests de integración.
    No persiste en base de datos.
    """
    raw_snapshot = body.snapshot.model_dump()
    raw_habits   = body.habits.model_dump() if body.habits else {}
    day          = raw_snapshot.get("capturedAt", "")[:10] or date.today().isoformat()

    readiness = _run_pipeline(raw_snapshot, raw_habits, body.lang, day)
    return {"data": readiness, "error": None}


@router.post("/snapshot")
def ingest_snapshot(snapshot: GarminSnapshot):
    """
    Ingesta un snapshot de Garmin y lo persiste.
    Llamado por el Garmin bridge o el mock en dev.
    """
    user_id = "default"
    data    = snapshot.model_dump()
    db.save_snapshot(user_id, data)
    log_snapshot_ingested(data, user_id)
    return {"data": {"capturedAt": snapshot.capturedAt}, "error": None}
