"""
ReadyDay — Score Engine (Python)
Puerto directo de las funciones JS en mvp/index.html.
Mismos pesos, mismos umbrales, misma lógica.
Funciones puras — sin efectos secundarios, sin imports de DB.

Responsabilidad única: CÁLCULO MATEMÁTICO de scores.
  - topFactors      → explanation_engine.py
  - insight/prediction → explanation_engine.py
  - recommendation  → recommendation_engine.py
"""

from typing import Literal

Zone = Literal["green", "yellow", "red"]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def clamp(v: float, a: float, b: float) -> float:
    return max(a, min(b, v))


def hr_score(hr: float) -> float:
    """
    Convierte HR en reposo a score de recuperación (0-100).
    Puerto de hrScore() del HTML MVP.
    """
    if hr <= 50: return 100
    if hr <= 55: return 90
    if hr <= 60: return 75
    if hr <= 65: return 55
    if hr <= 70: return 35
    return 20


def hab_penalty(habits: dict) -> float:
    """
    Calcula penalización total por hábitos (0-100).
    Puerto de habPen() del HTML MVP.

    habits = {
        "caffeineLate": {"cups": int, "lastTime": str|None},
        "alcohol":      {"drinks": int},
        "lateDinner":   {"ate": bool, "time": str|None}
    }
    Pesos: café +8/taza (max 28), alcohol +13/bebida (max 35), cena +7/13/20
    """
    # Cafeína tardía
    caffeine = habits.get("caffeineLate", {})
    if isinstance(caffeine, dict):
        cups = caffeine.get("cups", 0) or 0
    else:
        cups = 2 if caffeine else 0
    c_penalty = min(cups * 8, 28)

    # Alcohol
    alcohol = habits.get("alcohol", {})
    if isinstance(alcohol, dict):
        drinks = alcohol.get("drinks", 0) or 0
    else:
        drinks = 2 if alcohol else 0
    a_penalty = min(drinks * 13, 35)

    # Cena tardía
    dinner = habits.get("lateDinner", {})
    if isinstance(dinner, dict):
        ate = dinner.get("ate", False) or False
        time = dinner.get("time", "22:00") or "22:00"
    else:
        ate = bool(dinner)
        time = "22:00"

    if ate:
        if time == "23:00+":
            d_penalty = 20
        elif time == "22:00":
            d_penalty = 13
        else:
            d_penalty = 7
    else:
        d_penalty = 0

    return min(c_penalty + a_penalty + d_penalty, 100)


# ─────────────────────────────────────────────
# SCORE ENGINE CORE
# ─────────────────────────────────────────────

def calculate_recovery(snapshot: dict, habits: dict | None = None) -> int:
    """
    Recovery Score (0-100).
    Puerto de calcRec() del HTML MVP.

    Fórmula: 0.35×BB + 0.25×(100-Stress) + 0.20×HRscore + 0.20×Sleep
    """
    bb     = float(snapshot.get("bodyBattery") or 50)
    stress = float(snapshot.get("stressAvg")   or 50)
    hr     = float(snapshot.get("hrResting")   or 65)
    sleep  = float(snapshot.get("sleepScore")  or 50)

    score = (
        0.35 * bb +
        0.25 * (100 - stress) +
        0.20 * hr_score(hr) +
        0.20 * sleep
    )
    return round(clamp(score, 0, 100))


def calculate_strain(snapshot: dict, habits: dict | None = None) -> int:
    """
    Strain Score (0-100).
    Puerto de calcStr() del HTML MVP.

    Fórmula: 0.40×ActivityLoad + 0.25×RecoveryTimePenalty + 0.20×Stress + 0.15×HabitPenalty

    Recovery time penalty:
      ≥48h → 85 | ≥36h → 65 | ≥24h → 45 | ≥12h → 25 | else → 10
    """
    activity = float(snapshot.get("activityLoad")    or 0)
    rt_h     = float(snapshot.get("recoveryTimeH")   or 0)
    stress   = float(snapshot.get("stressAvg")       or 50)
    h        = habits or {}

    if rt_h >= 48:   rt_penalty = 85
    elif rt_h >= 36: rt_penalty = 65
    elif rt_h >= 24: rt_penalty = 45
    elif rt_h >= 12: rt_penalty = 25
    else:            rt_penalty = 10

    hp = hab_penalty(h)

    score = (
        0.40 * activity +
        0.25 * rt_penalty +
        0.20 * stress +
        0.15 * hp
    )
    return round(clamp(score, 0, 100))


def calculate_balance(recovery: int, strain: int) -> int:
    """
    Balance = Recovery - round(Strain/2)
    Puerto de calcBal() del HTML MVP.
    """
    return recovery - round(strain / 2)


def get_zone(recovery: int, balance: int) -> Zone:
    """
    Zona de readiness.
    Puerto de getZone() del HTML MVP.
    green: rec≥70 AND bal≥20
    yellow: rec≥45
    red: resto
    """
    if recovery >= 70 and balance >= 20:
        return "green"
    if recovery >= 45:
        return "yellow"
    return "red"


def compute_daily_readiness(snapshot: dict, habits: dict | None = None) -> dict:
    """
    Función principal del score engine — solo cálculo matemático.
    Entrada: CleanSnapshot (normalizado) + habits
    Salida: scores calculados SIN textos ni factores
      → topFactors   : explanation_engine.get_top_factors()
      → insight      : explanation_engine.get_insight()
      → prediction   : explanation_engine.get_prediction()
      → recommendation: recommendation_engine.get_recommendation()
    """
    h = habits or {}
    recovery = calculate_recovery(snapshot, h)
    strain   = calculate_strain(snapshot, h)
    balance  = calculate_balance(recovery, strain)
    zone     = get_zone(recovery, balance)

    return {
        "bodyBattery":   snapshot.get("bodyBattery"),
        "sleepScore":    snapshot.get("sleepScore"),
        "sleepHours":    snapshot.get("sleepHours"),
        "hrResting":     snapshot.get("hrResting"),
        "stressAvg":     snapshot.get("stressAvg"),
        "activityLoad":  snapshot.get("activityLoad"),
        "recoveryTimeH": snapshot.get("recoveryTimeH"),
        "recoveryScore": recovery,
        "strainScore":   strain,
        "balanceScore":  balance,
        "zone":          zone,
    }
