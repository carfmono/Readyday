"""
ReadyDay — Feature Flags
Activación/desactivación de funciones via variables de entorno.
Sin sistema complejo — lectura directa de env vars al arrancar.

Uso:
    from feature_flags import flags
    if flags.PREDICTION:
        ...

Para activar en dev: export FEATURE_PREDICTION=true
Para desactivar:     export FEATURE_PREDICTION=false
"""

import os
from dataclasses import dataclass


def _flag(name: str, default: bool = True) -> bool:
    val = os.getenv(name, "true" if default else "false")
    return val.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class FeatureFlags:
    """
    Flags disponibles. Todos True por defecto salvo ADVANCED_FACTORS.
    Cambiar en .env o en variables de entorno de Railway/Render.
    """

    # Muestra el bloque de predicción en la respuesta y en la UI
    PREDICTION: bool

    # Activa factorExplanations detalladas (para modal "Ver por qué")
    FACTOR_EXPLANATIONS: bool

    # Incluye confidenceScore en la respuesta
    CONFIDENCE_SCORE: bool

    # Factores avanzados adicionales (futuro — desactivado hasta Sprint 5)
    ADVANCED_FACTORS: bool

    # Guarda cada cálculo en DB automáticamente al hit /scores/today
    AUTO_PERSIST: bool


def _load() -> FeatureFlags:
    return FeatureFlags(
        PREDICTION          = _flag("FEATURE_PREDICTION",           default=True),
        FACTOR_EXPLANATIONS = _flag("FEATURE_FACTOR_EXPLANATIONS",  default=True),
        CONFIDENCE_SCORE    = _flag("FEATURE_CONFIDENCE_SCORE",     default=True),
        ADVANCED_FACTORS    = _flag("FEATURE_ADVANCED_FACTORS",     default=False),
        AUTO_PERSIST        = _flag("FEATURE_AUTO_PERSIST",         default=True),
    )


# Singleton — cargado una vez al arrancar el proceso
flags = _load()
