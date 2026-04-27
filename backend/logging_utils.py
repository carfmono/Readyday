"""
ReadyDay — Structured Decision Logger
Logging de decisiones sin acoplamiento a UI ni a HTTP.
Formato JSON — preparado para ingestión en Datadog / Logtail / stdout.
"""

import json
import logging
from datetime import datetime, timezone

# Logger nombrado — configurable desde main.py o desde la CLI
_logger = logging.getLogger("readyday.decisions")


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configura el handler básico de stdout.
    Llamar desde main.py una sola vez al arrancar.
    En prod, Railway / Render capturan stdout directamente.
    """
    if _logger.handlers:
        return  # evitar duplicados si se llama dos veces

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(level)


def log_decision(
    snapshot: dict,
    readiness: dict,
    confidence: int,
    missing_fields: list[str] | None = None,
) -> None:
    """
    Registra una decisión de readiness como entrada JSON estructurada.

    Campos incluidos:
    - ts, date, zone, recoveryScore, strainScore, balanceScore
    - confidenceScore, topFactors, recommendation
    - missingFields (campos que vinieron null de Garmin)
    - inputs (valores clave usados en el cálculo)
    """
    entry = {
        "ts":              datetime.now(timezone.utc).isoformat(),
        "date":            readiness.get("date"),
        "zone":            readiness.get("zone"),
        "recoveryScore":   readiness.get("recoveryScore"),
        "strainScore":     readiness.get("strainScore"),
        "balanceScore":    readiness.get("balanceScore"),
        "confidenceScore": confidence,
        "recommendation":  readiness.get("recommendation"),
        "topFactors":      readiness.get("topFactors", []),
        "missingFields":   missing_fields or [],
        "inputs": {
            "bodyBattery":   snapshot.get("bodyBattery"),
            "sleepScore":    snapshot.get("sleepScore"),
            "sleepHours":    snapshot.get("sleepHours"),
            "hrResting":     snapshot.get("hrResting"),
            "stressAvg":     snapshot.get("stressAvg"),
            "activityLoad":  snapshot.get("activityLoad"),
            "recoveryTimeH": snapshot.get("recoveryTimeH"),
        },
    }

    _logger.info(json.dumps(entry, ensure_ascii=False))


def log_snapshot_ingested(snapshot: dict, user_id: str = "default") -> None:
    """Registra la ingesta de un nuevo snapshot de Garmin."""
    entry = {
        "ts":          datetime.now(timezone.utc).isoformat(),
        "event":       "snapshot_ingested",
        "user_id":     user_id,
        "capturedAt":  snapshot.get("capturedAt"),
        "hasBodyBat":  snapshot.get("bodyBattery") is not None,
        "hasSleep":    snapshot.get("sleepScore") is not None,
        "hasHR":       snapshot.get("hrResting") is not None,
    }
    _logger.info(json.dumps(entry, ensure_ascii=False))


def log_override_applied(override: dict, day: str) -> None:
    """Registra cuando el usuario aplica un override de hábitos."""
    entry = {
        "ts":    datetime.now(timezone.utc).isoformat(),
        "event": "override_applied",
        "day":   day,
        "keys":  list(override.keys()),
    }
    _logger.info(json.dumps(entry, ensure_ascii=False))
