"""
ReadyDay — Recommendation Engine
Responsabilidad única: decisión principal (copy corto de acción diaria).

  "Hoy entrena fuerte" / "Hoy entrena moderado" / "Hoy descansa"

Para insight, prediction y topFactors → explanation_engine.py
"""

from typing import Literal

Zone = Literal["green", "yellow", "red"]
Lang = Literal["es", "en"]


def get_recommendation(zone: Zone, snapshot: dict, lang: Lang = "es") -> str:
    """
    Texto de decisión principal.
    Puerto de decision(z, d) del HTML MVP.
    """
    e = lang == "es"
    activity = float(snapshot.get("activityLoad") or 0)

    if zone == "green":
        return "Hoy entrena fuerte" if e else "Train hard today"
    if zone == "yellow":
        if activity > 60:
            return "Hoy entrena suave" if e else "Go light today"
        return "Hoy entrena moderado" if e else "Train moderate today"
    return "Hoy descansa" if e else "Rest today"
