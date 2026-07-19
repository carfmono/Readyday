import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, DeviceSnapshot, DailyScore
from schemas import SnapshotIn, SnapshotOut, ScoreOut
from auth import get_current_user
from services.score_engine import compute_daily_readiness
from services.explanation_engine import generate_explanation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


def _snapshot_to_dict(snap: DeviceSnapshot) -> dict:
    return {
        "body_battery": snap.body_battery,
        "sleep_score":  snap.sleep_score,
        "sleep_hours":  snap.sleep_hours,
        "hr_resting":   snap.hr_resting,
        "stress_avg":   snap.stress_avg,
        "activity_load": snap.activity_load,
        "recovery_time_h": snap.recovery_time_h,
    }


@router.post("", response_model=SnapshotOut, status_code=201)
async def post_snapshot(
    body: SnapshotIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Recibe un snapshot desde cualquier wearable (Garmin, Apple Watch, manual…).
    Calcula el score del día y lo persiste.
    Si ya hay un score para hoy, lo sobreescribe con los datos nuevos.
    """
    # Guardar snapshot
    snap = DeviceSnapshot(
        user_id=current_user.id,
        source=body.source,
        captured_at=body.captured_at,
        body_battery=body.body_battery,
        sleep_score=body.sleep_score,
        sleep_hours=body.sleep_hours,
        hr_resting=body.hr_resting,
        stress_avg=body.stress_avg,
        activity_load=body.activity_load,
        recovery_time_h=body.recovery_time_h,
        raw_payload=json.dumps(body.raw_payload) if body.raw_payload else None,
    )
    db.add(snap)
    db.flush()  # obtener snap.id antes del commit

    # Calcular score
    snap_dict = _snapshot_to_dict(snap)
    result = compute_daily_readiness(
        snapshot=snap_dict,
        caffeine_cups=body.caffeine_cups,
        alcohol_drinks=body.alcohol_drinks,
        late_dinner=body.late_dinner,
        energy_manual=body.energy_manual,
    )

    # Textos (Claude o plantillas)
    texts = await generate_explanation(
        zone=result["zone"],
        factors=result["top_factors"],
        scores=result,
        lang=current_user.lang,
    )

    # Fecha del snapshot (día local aproximado desde captured_at UTC)
    date_str = body.captured_at.date().isoformat()

    # Upsert daily score
    existing = db.query(DailyScore).filter(
        DailyScore.user_id == current_user.id,
        DailyScore.date == date_str,
    ).first()

    if existing:
        score_obj = existing
        score_obj.snapshot_id   = snap.id
        score_obj.computed_at   = datetime.now(timezone.utc)
    else:
        score_obj = DailyScore(user_id=current_user.id, date=date_str, snapshot_id=snap.id)
        db.add(score_obj)

    score_obj.recovery_score = result["recovery_score"]
    score_obj.strain_score   = result["strain_score"]
    score_obj.balance_score  = result["balance_score"]
    score_obj.zone           = result["zone"]
    score_obj.confidence     = result["confidence"]
    score_obj.recommendation = texts.get("recommendation")
    score_obj.insight        = texts.get("insight")
    score_obj.top_factors    = json.dumps(result["top_factors"])
    score_obj.caffeine_cups  = body.caffeine_cups
    score_obj.alcohol_drinks = body.alcohol_drinks
    score_obj.late_dinner    = body.late_dinner
    score_obj.energy_manual  = body.energy_manual

    db.commit()
    db.refresh(score_obj)

    score_out = _build_score_out(score_obj, snap)
    return SnapshotOut(snapshot_id=snap.id, score=score_out)


def _build_score_out(score: DailyScore, snap: DeviceSnapshot) -> ScoreOut:
    return ScoreOut(
        id=score.id,
        date=score.date,
        recovery_score=score.recovery_score,
        strain_score=score.strain_score,
        balance_score=score.balance_score,
        zone=score.zone,
        confidence=score.confidence,
        recommendation=score.recommendation,
        insight=score.insight,
        top_factors=json.loads(score.top_factors) if score.top_factors else [],
        body_battery=snap.body_battery,
        sleep_score=snap.sleep_score,
        sleep_hours=snap.sleep_hours,
        hr_resting=snap.hr_resting,
        stress_avg=snap.stress_avg,
        activity_load=snap.activity_load,
        recovery_time_h=snap.recovery_time_h,
        source=snap.source,
    )
