"""
Score Engine — cálculo puro sin efectos secundarios.
Fórmulas portadas del MVP HTML original + revisadas.
"""

from typing import Literal

Zone = Literal["green", "yellow", "red"]


def clamp(v: float, a: float, b: float) -> float:
    return max(a, min(b, v))


def hr_score(hr: float) -> float:
    """HR en reposo → score 0-100 (mayor HR = menor score)."""
    if hr <= 50: return 100
    if hr <= 55: return 90
    if hr <= 60: return 75
    if hr <= 65: return 55
    if hr <= 70: return 35
    return 20


def habit_penalty(caffeine_cups: int, alcohol_drinks: int, late_dinner: bool) -> float:
    """Penalización total por hábitos (0-100)."""
    c = min(caffeine_cups * 8, 28)
    a = min(alcohol_drinks * 13, 35)
    d = 13 if late_dinner else 0
    return min(c + a + d, 100)


def calculate_recovery(snapshot: dict) -> int:
    """Recovery Score 0-100. Fórmula: 0.35×BB + 0.25×(100-Stress) + 0.20×HRscore + 0.20×Sleep"""
    bb    = float(snapshot.get("body_battery") or 50)
    stress = float(snapshot.get("stress_avg") or 50)
    hr    = float(snapshot.get("hr_resting") or 65)
    sleep = float(snapshot.get("sleep_score") or 50)

    # Redistribuir pesos cuando faltan datos
    fields_present = sum([
        snapshot.get("body_battery") is not None,
        snapshot.get("stress_avg") is not None,
        snapshot.get("hr_resting") is not None,
        snapshot.get("sleep_score") is not None,
    ])

    score = (
        0.35 * bb +
        0.25 * (100 - stress) +
        0.20 * hr_score(hr) +
        0.20 * sleep
    )
    return round(clamp(score, 0, 100))


def calculate_strain(snapshot: dict, caffeine_cups: int = 0, alcohol_drinks: int = 0, late_dinner: bool = False) -> int:
    """Strain Score 0-100. Fórmula: 0.40×Activity + 0.25×RecoveryTimePenalty + 0.20×Stress + 0.15×HabitPenalty"""
    activity = float(snapshot.get("activity_load") or 0)
    rt_h     = float(snapshot.get("recovery_time_h") or 0)
    stress   = float(snapshot.get("stress_avg") or 50)

    if rt_h >= 48:   rt_penalty = 85
    elif rt_h >= 36: rt_penalty = 65
    elif rt_h >= 24: rt_penalty = 45
    elif rt_h >= 12: rt_penalty = 25
    else:            rt_penalty = 10

    hp = habit_penalty(caffeine_cups, alcohol_drinks, late_dinner)

    score = (
        0.40 * activity +
        0.25 * rt_penalty +
        0.20 * stress +
        0.15 * hp
    )
    return round(clamp(score, 0, 100))


def calculate_balance(recovery: int, strain: int) -> float:
    return round(recovery - strain / 2, 1)


def get_zone(recovery: int, balance: float) -> Zone:
    if recovery >= 70 and balance >= 20:
        return "green"
    if recovery >= 45:
        return "yellow"
    return "red"


def confidence_score(snapshot: dict) -> int:
    """Qué tan completo está el snapshot (0-100)."""
    key_fields = ["body_battery", "sleep_score", "hr_resting", "stress_avg"]
    bonus_fields = ["sleep_hours", "activity_load", "recovery_time_h"]
    present = sum(1 for f in key_fields if snapshot.get(f) is not None)
    bonus = sum(1 for f in bonus_fields if snapshot.get(f) is not None)
    base = (present / len(key_fields)) * 80
    return round(min(100, base + bonus * 5))


def get_top_factors(snapshot: dict, caffeine_cups: int = 0, alcohol_drinks: int = 0, late_dinner: bool = False) -> list[str]:
    """Retorna hasta 3 factores más relevantes para explicar el score."""
    factors = []

    bb = snapshot.get("body_battery")
    if bb is not None:
        if bb < 30:   factors.append(("bb", "bajo"))
        elif bb > 80: factors.append(("bb", "alto"))

    sleep = snapshot.get("sleep_score")
    if sleep is not None:
        if sleep < 50: factors.append(("sleep", "bajo"))
        elif sleep > 80: factors.append(("sleep", "alto"))

    stress = snapshot.get("stress_avg")
    if stress is not None:
        if stress > 70: factors.append(("stress", "alto"))

    hr = snapshot.get("hr_resting")
    if hr is not None:
        if hr > 70: factors.append(("hr", "alto"))

    rt = snapshot.get("recovery_time_h")
    if rt is not None and rt > 24:
        factors.append(("recovery_time", "alto"))

    if caffeine_cups >= 2: factors.append(("habits_caffeine", "presente"))
    if alcohol_drinks >= 1: factors.append(("habits_alcohol", "presente"))
    if late_dinner:         factors.append(("habits_dinner", "tarde"))

    # Retorna solo los nombres de los top 3
    return [f[0] for f in factors[:3]]


def compute_daily_readiness(
    snapshot: dict,
    caffeine_cups: int = 0,
    alcohol_drinks: int = 0,
    late_dinner: bool = False,
    energy_manual: int | None = None,
) -> dict:
    """Punto de entrada principal del score engine."""
    recovery = calculate_recovery(snapshot)
    strain   = calculate_strain(snapshot, caffeine_cups, alcohol_drinks, late_dinner)
    balance  = calculate_balance(recovery, strain)
    zone     = get_zone(recovery, balance)
    conf     = confidence_score(snapshot)
    factors  = get_top_factors(snapshot, caffeine_cups, alcohol_drinks, late_dinner)

    # Override manual de energía ajusta el recovery
    if energy_manual is not None:
        energy_map = {0: -20, 1: -10, 2: 0, 3: 10, 4: 20}
        delta = energy_map.get(energy_manual, 0)
        recovery = round(clamp(recovery + delta, 0, 100))
        balance  = calculate_balance(recovery, strain)
        zone     = get_zone(recovery, balance)

    return {
        "recovery_score": recovery,
        "strain_score":   strain,
        "balance_score":  balance,
        "zone":           zone,
        "confidence":     conf,
        "top_factors":    factors,
    }
