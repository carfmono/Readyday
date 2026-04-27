"""
ReadyDay — Explanation Engine
Responsable de: topFactors, insight, prediction, factor_explanations.

Separado del recommendation_engine (que solo tiene la decisión corta).
Puerto del urgency sort de renderToday() + insight/prediction del HTML MVP.
"""

from typing import Literal
from score_engine import hab_penalty

Zone = Literal["green", "yellow", "red"]
Lang = Literal["es", "en"]


# ─────────────────────────────────────────────
# TOP FACTORS
# ─────────────────────────────────────────────

def get_top_factors(snapshot: dict, habits: dict | None = None, max_n: int = 3) -> list[str]:
    """
    Devuelve los factores más urgentes (más alejados del óptimo).
    Puerto del urgency sort de renderToday() del HTML MVP + factor 'habits'.
    Devuelve lista de FactorKey strings, máx max_n.
    """
    bb     = float(snapshot.get("bodyBattery")   or 50)
    sleep  = float(snapshot.get("sleepScore")    or 50)
    stress = float(snapshot.get("stressAvg")     or 50)
    hr     = float(snapshot.get("hrResting")     or 65)
    act    = float(snapshot.get("activityLoad")  or 0)
    rt     = float(snapshot.get("recoveryTimeH") or 0)
    hp     = float(hab_penalty(habits or {}))

    urgency: dict[str, float] = {
        "bb":     100.0 - bb,
        "sleep":  100.0 - sleep,
        "stress": stress,
        "hr":     max(0.0, (hr - 55) * 3),
        "act":    act,
        "rt":     min(rt * 2, 100.0),
        "habits": hp,
    }

    return [k for k, _ in sorted(urgency.items(), key=lambda x: x[1], reverse=True)[:max_n]]


# ─────────────────────────────────────────────
# INSIGHT
# ─────────────────────────────────────────────

def get_insight(zone: Zone, snapshot: dict, habits: dict, lang: Lang = "es") -> str:
    """
    Texto de insight contextual.
    Puerto de insight(z, d, h) del HTML MVP.
    Evita frases genéricas — usa condiciones específicas.
    """
    e = lang == "es"

    caffeine = habits.get("caffeineLate", {})
    cups = (caffeine.get("cups", 0) if isinstance(caffeine, dict) else (2 if caffeine else 0)) or 0

    alcohol = habits.get("alcohol", {})
    drinks = (alcohol.get("drinks", 0) if isinstance(alcohol, dict) else (2 if alcohol else 0)) or 0

    sleep_score   = float(snapshot.get("sleepScore")   or 50)
    body_battery  = float(snapshot.get("bodyBattery")  or 50)

    if zone == "green":
        return (
            "Tus reservas están altas y el estrés bajo control. Es un buen día para dar el máximo."
            if e else
            "Reserves are high and stress is under control. A good day to give your best."
        )

    if zone == "yellow":
        if sleep_score < 60:
            return (
                "Tu recuperación aún no es completa. Evita alta intensidad hoy. ⚠️"
                if e else
                "Your recovery isn't complete yet. Avoid high intensity today. ⚠️"
            )
        if cups > 2:
            return (
                "La cafeína tardía afectó tu sueño. Moderado es lo correcto hoy."
                if e else
                "Late caffeine affected your sleep. Moderate effort is right today."
            )
        if drinks > 0:
            return (
                "El alcohol de ayer redujo tu recuperación nocturna. Ve con cuidado."
                if e else
                "Last night's alcohol reduced your overnight recovery. Take it easy."
            )
        return (
            "Estás listo para avanzar, pero no para exigirte al máximo."
            if e else
            "You're ready to move forward, but not to push to the limit."
        )

    # zone == "red"
    if body_battery < 30:
        return (
            "Batería muy baja. El descanso de hoy es la mejor inversión para mañana."
            if e else
            "Battery very low. Today's rest is the best investment for tomorrow."
        )
    return (
        "Tu cuerpo necesita recuperarse. Forzar hoy puede costarte varios días."
        if e else
        "Your body needs to recover. Pushing today could cost you several days."
    )


# ─────────────────────────────────────────────
# PREDICTION
# ─────────────────────────────────────────────

def get_prediction(zone: Zone, lang: Lang = "es") -> str:
    """
    Texto de predicción: qué pasa si sigues la recomendación.
    Puerto de prediction(z) del HTML MVP.
    """
    e = lang == "es"

    if zone == "green":
        return (
            "Si entrenas fuerte hoy → mañana las reservas bajarán, pero habrás invertido en rendimiento real."
            if e else
            "Train hard today → tomorrow reserves drop, but you'll have invested in real performance."
        )
    if zone == "yellow":
        return (
            "Si entrenas moderado hoy → mañana podrías mejorar tu recuperación +8 a +12 pts."
            if e else
            "Train moderate today → tomorrow your recovery could improve +8 to +12 pts."
        )
    return (
        "Si descansas hoy → mañana podrías recuperar entre +10 y +18 puntos."
        if e else
        "Rest today → tomorrow you could recover +10 to +18 points."
    )


# ─────────────────────────────────────────────
# FACTOR EXPLANATIONS — para modal "Ver por qué"
# ─────────────────────────────────────────────

def get_factor_explanations(
    top_factors: list[str],
    snapshot: dict,
    habits: dict | None = None,
    lang: Lang = "es",
) -> list[dict]:
    """
    Genera explicaciones legibles para cada factor del modal "Ver por qué".
    Formato V2: { key, impact, text }
    impact es siempre 'negative' para topFactors (son los más urgentes/problemáticos).
    """
    e = lang == "es"
    h = habits or {}
    result = []

    for key in top_factors:
        if key == "bb":
            val = float(snapshot.get("bodyBattery") or 50)
            text = (
                f"Body Battery en {val:.0f}/100. "
                + ("Nivel bajo — el cuerpo aún procesa el esfuerzo reciente."
                   if val < 40 else
                   "Nivel moderado — no está al tope, hay margen de mejora.")
            ) if e else (
                f"Body Battery at {val:.0f}/100. "
                + ("Low — your body is still processing recent effort."
                   if val < 40 else
                   "Moderate — not at full, room to improve.")
            )

        elif key == "sleep":
            val = float(snapshot.get("sleepScore") or 50)
            text = (
                f"Score de sueño: {val:.0f}/100. "
                + ("Sueño insuficiente — la recuperación nocturna no fue completa."
                   if val < 60 else
                   "Sueño aceptable pero con margen de mejora.")
            ) if e else (
                f"Sleep score: {val:.0f}/100. "
                + ("Insufficient — overnight recovery wasn't complete."
                   if val < 60 else
                   "Acceptable but room to improve.")
            )

        elif key == "stress":
            val = float(snapshot.get("stressAvg") or 50)
            text = (
                f"Estrés promedio de ayer: {val:.0f}/100. "
                + ("Nivel elevado — el sistema nervioso necesita calma."
                   if val > 60 else
                   "Nivel moderado — manejable pero presente.")
            ) if e else (
                f"Average stress yesterday: {val:.0f}/100. "
                + ("High — the nervous system needs calm."
                   if val > 60 else
                   "Moderate — manageable but present.")
            )

        elif key == "hr":
            val = float(snapshot.get("hrResting") or 65)
            text = (
                f"FC en reposo: {val:.0f} bpm. "
                + ("Alta para tu nivel — señal de carga acumulada o recuperación incompleta."
                   if val > 65 else
                   "Ligeramente elevada — el corazón aún no está en su mejor punto.")
            ) if e else (
                f"Resting HR: {val:.0f} bpm. "
                + ("High for your level — sign of accumulated load or incomplete recovery."
                   if val > 65 else
                   "Slightly elevated — heart isn't at its best yet.")
            )

        elif key == "act":
            val = float(snapshot.get("activityLoad") or 0)
            text = (
                f"Carga de actividad acumulada: {val:.0f}/100. "
                + ("Alta — el cuerpo aún digiere el entrenamiento reciente."
                   if val > 60 else
                   "Moderada — presente pero manejable.")
            ) if e else (
                f"Accumulated activity load: {val:.0f}/100. "
                + ("High — your body is still digesting recent training."
                   if val > 60 else
                   "Moderate — present but manageable.")
            )

        elif key == "rt":
            val = float(snapshot.get("recoveryTimeH") or 0)
            text = (
                f"Tiempo estimado de recuperación: {val:.0f}h. "
                + ("Necesitas más descanso antes de volver a exigirte al máximo."
                   if val > 24 else
                   "Casi listo — pocas horas más completarán la recuperación.")
            ) if e else (
                f"Estimated recovery time: {val:.0f}h. "
                + ("You need more rest before pushing hard again."
                   if val > 24 else
                   "Almost there — a few more hours will complete recovery.")
            )

        elif key == "habits":
            hp = hab_penalty(h)
            caffeine = h.get("caffeineLate", {})
            cups = (caffeine.get("cups", 0) if isinstance(caffeine, dict) else 0) or 0
            alcohol = h.get("alcohol", {})
            drinks = (alcohol.get("drinks", 0) if isinstance(alcohol, dict) else 0) or 0

            parts_es, parts_en = [], []
            if cups > 0:
                parts_es.append(f"{cups} café{'s' if cups>1 else ''} tarde")
                parts_en.append(f"{cups} late coffee{'s' if cups>1 else ''}")
            if drinks > 0:
                parts_es.append(f"{drinks} bebida{'s' if drinks>1 else ''} alcohólica{'s' if drinks>1 else ''}")
                parts_en.append(f"{drinks} alcoholic drink{'s' if drinks>1 else ''}")
            dinner = h.get("lateDinner", {})
            if isinstance(dinner, dict) and dinner.get("ate"):
                parts_es.append("cena tarde")
                parts_en.append("late dinner")

            causes_es = ", ".join(parts_es) if parts_es else "varios factores"
            causes_en = ", ".join(parts_en) if parts_en else "various factors"

            text = (
                f"Impacto de hábitos: -{hp} pts. Factores: {causes_es}."
            ) if e else (
                f"Habit impact: -{hp} pts. Factors: {causes_en}."
            )

        else:
            continue

        result.append({
            "key":    key,
            "impact": "negative",
            "text":   text,
        })

    return result


# ─────────────────────────────────────────────
# EXPLAIN — función principal
# ─────────────────────────────────────────────

def explain(
    zone: Zone,
    snapshot: dict,
    habits: dict | None = None,
    lang: Lang = "es",
    max_factors: int = 3,
    include_explanations: bool = True,
) -> dict:
    """
    Función principal — genera todo el contenido del "por qué".
    Retorna: topFactors, insight, prediction y (opcional) factorExplanations.
    """
    h = habits or {}
    top = get_top_factors(snapshot, h, max_factors)

    result: dict = {
        "topFactors": top,
        "insight":    get_insight(zone, snapshot, h, lang),
        "prediction": get_prediction(zone, lang),
    }

    if include_explanations:
        result["factorExplanations"] = get_factor_explanations(top, snapshot, h, lang)

    return result
