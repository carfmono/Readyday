"""
Scheduler — job mañanero que sincroniza Garmin y envía push notifications.
Se ejecuta a la hora configurada (NOTIFICATION_HOUR, default 7am servidor).
"""

import logging
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()


async def morning_sync():
    """
    Corre cada mañana:
    1. Para cada usuario con Garmin conectado: pull del snapshot de hoy
    2. Calcula score si no existe para hoy
    3. Envía push notification a tokens activos
    """
    from database import SessionLocal
    from models import User, UserDevice, DailyScore, PushToken
    from services.garmin_service import decrypt_credentials, fetch_snapshot
    from services.score_engine import compute_daily_readiness
    from services.explanation_engine import generate_explanation
    from services.notification_service import send_score_notification
    from routers.snapshots import _snapshot_to_dict
    from models import DeviceSnapshot
    import json

    logger.info("morning_sync iniciado — %s", datetime.utcnow().isoformat())
    db = SessionLocal()
    today = date.today().isoformat()
    sent = 0

    try:
        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            # Pull Garmin si tiene credenciales y no hay score de hoy
            existing_score = db.query(DailyScore).filter(
                DailyScore.user_id == user.id,
                DailyScore.date == today,
            ).first()

            if not existing_score:
                garmin_device = db.query(UserDevice).filter(
                    UserDevice.user_id == user.id,
                    UserDevice.source == "garmin",
                    UserDevice.is_connected == True,
                    UserDevice.encrypted_credentials.isnot(None),
                ).first()

                if garmin_device:
                    creds = decrypt_credentials(garmin_device.encrypted_credentials)
                    if creds:
                        try:
                            snap_data = await fetch_snapshot(user.id, creds[0], creds[1])
                            snap = DeviceSnapshot(
                                user_id=user.id,
                                source="garmin",
                                captured_at=datetime.utcnow(),
                                body_battery=snap_data.get("body_battery"),
                                sleep_score=snap_data.get("sleep_score"),
                                sleep_hours=snap_data.get("sleep_hours"),
                                hr_resting=snap_data.get("hr_resting"),
                                stress_avg=snap_data.get("stress_avg"),
                                activity_load=snap_data.get("activity_load"),
                                recovery_time_h=snap_data.get("recovery_time_h"),
                            )
                            db.add(snap)
                            db.flush()

                            result = compute_daily_readiness(_snapshot_to_dict(snap))
                            texts = await generate_explanation(result["zone"], result["top_factors"], result, user.lang)

                            existing_score = DailyScore(
                                user_id=user.id,
                                date=today,
                                snapshot_id=snap.id,
                                recovery_score=result["recovery_score"],
                                strain_score=result["strain_score"],
                                balance_score=result["balance_score"],
                                zone=result["zone"],
                                confidence=result["confidence"],
                                recommendation=texts.get("recommendation"),
                                insight=texts.get("insight"),
                                top_factors=json.dumps(result["top_factors"]),
                            )
                            db.add(existing_score)
                            db.commit()
                            db.refresh(existing_score)
                            logger.info("Score calculado para user %s: zona=%s", user.id, existing_score.zone)
                        except Exception as e:
                            logger.warning("Garmin sync falló para user %s: %s", user.id, e)
                            db.rollback()

            # Enviar push si hay score
            if existing_score:
                tokens = db.query(PushToken).filter(
                    PushToken.user_id == user.id,
                    PushToken.is_active == True,
                    PushToken.platform == "android",
                ).all()

                for token_obj in tokens:
                    if existing_score.push_sent_at and existing_score.push_sent_at.date() == date.today():
                        continue  # ya enviada hoy

                    ok = await send_score_notification(
                        token=token_obj.token,
                        recovery_score=existing_score.recovery_score,
                        zone=existing_score.zone,
                        lang=user.lang,
                    )
                    if ok:
                        existing_score.push_sent_at = datetime.utcnow()
                        token_obj.last_used_at = datetime.utcnow()
                        db.commit()
                        sent += 1

    except Exception as e:
        logger.error("morning_sync error: %s", e)
    finally:
        db.close()

    logger.info("morning_sync completado — %d notificaciones enviadas", sent)


def start_scheduler():
    scheduler.add_job(
        morning_sync,
        trigger=CronTrigger(hour=settings.notification_hour, minute=settings.notification_minute),
        id="morning_sync",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info(
        "Scheduler iniciado — morning_sync a las %02d:%02d",
        settings.notification_hour,
        settings.notification_minute,
    )
