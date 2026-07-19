"""
Push Notification Service — FCM (Firebase Cloud Messaging).
Si FCM_SERVER_KEY no está configurado, las notificaciones se omiten silenciosamente.
"""

import logging
import httpx
from datetime import datetime
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send"

ZONE_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
ZONE_ACTION = {
    "green": {"es": "Día para entrenar fuerte", "en": "Day to push hard"},
    "yellow": {"es": "Entrena con moderación", "en": "Train moderately"},
    "red": {"es": "Descansa hoy", "en": "Rest today"},
}


async def send_score_notification(
    token: str,
    recovery_score: int,
    zone: str,
    lang: str = "es",
) -> bool:
    """Envía push notification con el score del día. Retorna True si fue exitoso."""
    if not settings.fcm_server_key:
        logger.debug("FCM_SERVER_KEY no configurado — notificación omitida")
        return False

    emoji = ZONE_EMOJI.get(zone, "🟡")
    action = ZONE_ACTION.get(zone, ZONE_ACTION["yellow"]).get(lang, ZONE_ACTION["yellow"]["es"])

    title = f"ReadyDay — Score {recovery_score} {emoji}"
    body = action

    payload = {
        "to": token,
        "notification": {
            "title": title,
            "body": body,
            "sound": "default",
            "icon": "ic_notification",
            "color": "#00D4AA",
        },
        "data": {
            "type": "daily_score",
            "recovery_score": str(recovery_score),
            "zone": zone,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "priority": "high",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                FCM_ENDPOINT,
                json=payload,
                headers={
                    "Authorization": f"key={settings.fcm_server_key}",
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()
            if data.get("success") == 1:
                logger.info("Push enviado a token ...%s zona=%s score=%d", token[-6:], zone, recovery_score)
                return True
            else:
                logger.warning("FCM error: %s", data)
                return False
    except Exception as e:
        logger.error("Error enviando push: %s", e)
        return False


async def send_bulk_notifications(tokens_and_scores: list[dict]) -> int:
    """Envía notificaciones en masa. Retorna count de enviadas."""
    sent = 0
    for item in tokens_and_scores:
        ok = await send_score_notification(
            token=item["token"],
            recovery_score=item["recovery_score"],
            zone=item["zone"],
            lang=item.get("lang", "es"),
        )
        if ok:
            sent += 1
    return sent
