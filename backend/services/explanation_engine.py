"""
Explanation Engine — textos en lenguaje natural vía Claude API.
Si la API key no está configurada, retorna plantillas en texto plano.
"""

import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ZONE_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}

TEMPLATES = {
    "es": {
        "green": {
            "recommendation": "Hoy estás en zona verde. Tu cuerpo está recuperado — es buen día para entrenar fuerte o exigirte.",
            "insight": "Tu recuperación está por encima del umbral óptimo. Aprovecha el día.",
        },
        "yellow": {
            "recommendation": "Zona amarilla. Entrena, pero con moderación — nada de máximos hoy.",
            "insight": "Tu cuerpo está en recuperación parcial. Un entrenamiento moderado es lo más inteligente.",
        },
        "red": {
            "recommendation": "Zona roja. Descansa activamente hoy — caminar, estirar, nada intenso.",
            "insight": "Tus métricas de recuperación están bajas. Forzar hoy retrasa la recuperación del mañana.",
        },
    },
    "en": {
        "green": {
            "recommendation": "You're in the green zone. Your body is recovered — great day to push hard.",
            "insight": "Your recovery is above optimal threshold. Take advantage of today.",
        },
        "yellow": {
            "recommendation": "Yellow zone. Train, but keep it moderate — no PRs today.",
            "insight": "Your body is in partial recovery. A moderate workout is the smart call.",
        },
        "red": {
            "recommendation": "Red zone. Active rest today — walk, stretch, nothing intense.",
            "insight": "Your recovery metrics are low. Pushing today delays tomorrow's recovery.",
        },
    },
}

FACTOR_LABELS = {
    "es": {
        "bb": "Batería corporal baja",
        "sleep": "Sueño insuficiente",
        "stress": "Estrés elevado",
        "hr": "FC en reposo alta",
        "recovery_time": "Tiempo de recuperación pendiente",
        "habits_caffeine": "Cafeína tardía",
        "habits_alcohol": "Alcohol reciente",
        "habits_dinner": "Cena tardía",
    },
    "en": {
        "bb": "Low body battery",
        "sleep": "Poor sleep",
        "stress": "High stress",
        "hr": "Elevated resting HR",
        "recovery_time": "Recovery time pending",
        "habits_caffeine": "Late caffeine",
        "habits_alcohol": "Recent alcohol",
        "habits_dinner": "Late dinner",
    },
}


def _template_texts(zone: str, lang: str) -> dict:
    lang = lang if lang in TEMPLATES else "es"
    zone = zone if zone in TEMPLATES[lang] else "yellow"
    return TEMPLATES[lang][zone]


async def generate_explanation(
    zone: str,
    factors: list[str],
    scores: dict,
    lang: str = "es",
) -> dict:
    """
    Genera recomendación + insight.
    Intenta Claude primero; cae en plantillas si no hay API key.
    """
    if not settings.anthropic_api_key:
        return _template_texts(zone, lang)

    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        factor_labels = FACTOR_LABELS.get(lang, FACTOR_LABELS["es"])
        factor_texts = [factor_labels.get(f, f) for f in factors]

        lang_name = "español" if lang == "es" else "English"
        prompt = f"""Eres el asistente de bienestar de ReadyDay. Genera en {lang_name} dos textos cortos para el usuario basándote en:

Zona de readiness: {zone} {ZONE_EMOJI.get(zone, '')}
Recovery score: {scores.get('recovery_score', '?')}/100
Strain score: {scores.get('strain_score', '?')}/100
Factores principales: {', '.join(factor_texts) if factor_texts else 'datos generales'}

Genera exactamente:
1. RECOMENDACIÓN (1 oración, acción concreta: qué hacer hoy con el entrenamiento)
2. INSIGHT (1 oración, explicación del por qué basada en los datos)

Tono: directo, cercano, sin jerga médica. Máximo 20 palabras cada uno.
Formato de respuesta:
RECOMENDACIÓN: [texto]
INSIGHT: [texto]"""

        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        text = msg.content[0].text.strip()
        rec_line = next((l for l in text.splitlines() if l.startswith("RECOMENDACIÓN:") or l.startswith("RECOMMENDATION:")), "")
        ins_line = next((l for l in text.splitlines() if l.startswith("INSIGHT:")), "")

        return {
            "recommendation": rec_line.split(":", 1)[-1].strip() if rec_line else _template_texts(zone, lang)["recommendation"],
            "insight": ins_line.split(":", 1)[-1].strip() if ins_line else _template_texts(zone, lang)["insight"],
        }

    except Exception as e:
        logger.warning("Claude API error, usando plantilla: %s", e)
        return _template_texts(zone, lang)
