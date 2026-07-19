import json
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, DailyScore, DeviceSnapshot
from schemas import ScoreOut, ScoreHistoryOut
from auth import get_current_user

router = APIRouter(prefix="/api/scores", tags=["scores"])


def _build_score_out(score: DailyScore, snap: DeviceSnapshot | None) -> ScoreOut:
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
        body_battery=snap.body_battery if snap else None,
        sleep_score=snap.sleep_score if snap else None,
        sleep_hours=snap.sleep_hours if snap else None,
        hr_resting=snap.hr_resting if snap else None,
        stress_avg=snap.stress_avg if snap else None,
        activity_load=snap.activity_load if snap else None,
        recovery_time_h=snap.recovery_time_h if snap else None,
        source=snap.source if snap else None,
    )


@router.get("/today", response_model=ScoreOut | None)
def get_today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today().isoformat()
    score = db.query(DailyScore).filter(
        DailyScore.user_id == current_user.id,
        DailyScore.date == today,
    ).first()

    if not score:
        return None

    snap = db.query(DeviceSnapshot).filter(DeviceSnapshot.id == score.snapshot_id).first() if score.snapshot_id else None
    return _build_score_out(score, snap)


@router.get("/history", response_model=ScoreHistoryOut)
def get_history(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    since = (date.today() - timedelta(days=days)).isoformat()
    scores = (
        db.query(DailyScore)
        .filter(DailyScore.user_id == current_user.id, DailyScore.date >= since)
        .order_by(DailyScore.date.desc())
        .all()
    )

    result = []
    for s in scores:
        snap = db.query(DeviceSnapshot).filter(DeviceSnapshot.id == s.snapshot_id).first() if s.snapshot_id else None
        result.append(_build_score_out(s, snap))

    return ScoreHistoryOut(scores=result, days=days)
