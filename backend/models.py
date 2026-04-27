"""
ReadyDay — Pydantic models
Espejo exacto de shared-types/readiness.ts
"""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# PRIMITIVES
# ─────────────────────────────────────────────

Zone = Literal["green", "yellow", "red"]
FactorKey = Literal["bb", "sleep", "stress", "hr", "act", "rt", "habits"]
Lang = Literal["es", "en"]
Goal = Literal["health", "performance", "longevity"]


# ─────────────────────────────────────────────
# HABITS
# ─────────────────────────────────────────────

class CaffeineLate(BaseModel):
    cups: int = 0
    lastTime: Optional[str] = None


class Alcohol(BaseModel):
    drinks: int = 0


class LateDinner(BaseModel):
    ate: bool = False
    time: Optional[str] = None


class HabitDefaults(BaseModel):
    caffeineLate: CaffeineLate = Field(default_factory=CaffeineLate)
    alcohol: Alcohol = Field(default_factory=Alcohol)
    lateDinner: LateDinner = Field(default_factory=LateDinner)


class HabitOverride(HabitDefaults):
    energyManual: Optional[int] = None  # 0-4 pill index


# ─────────────────────────────────────────────
# GARMIN SNAPSHOT
# ─────────────────────────────────────────────

class GarminSnapshot(BaseModel):
    capturedAt: str                         # ISO datetime
    bodyBattery: Optional[float] = None     # 0-100
    sleepScore: Optional[float] = None      # 0-100
    sleepHours: Optional[float] = None      # decimal hours
    hrResting: Optional[float] = None       # bpm
    stressAvg: Optional[float] = None       # 0-100
    activityLoad: Optional[float] = None    # 0-100
    recoveryTimeH: Optional[float] = None   # hours


# ─────────────────────────────────────────────
# DAILY READINESS
# ─────────────────────────────────────────────

class DailyReadiness(BaseModel):
    date: str                               # ISO date: "2025-04-22"

    # Input — datos Garmin (nullable)
    bodyBattery: Optional[float] = None
    sleepScore: Optional[float] = None
    sleepHours: Optional[float] = None
    hrResting: Optional[float] = None
    stressAvg: Optional[float] = None
    activityLoad: Optional[float] = None
    recoveryTimeH: Optional[float] = None

    # Output — scores calculados
    recoveryScore: int
    strainScore: int
    balanceScore: int
    zone: Zone

    # Output — confianza del cálculo (0-100)
    # 95 = todos los datos presentes | <65 = faltan métricas clave
    # None cuando el feature flag CONFIDENCE_SCORE está desactivado
    confidenceScore: Optional[int] = None

    # Output — textos
    recommendation: str
    insight: str
    prediction: Optional[str] = None

    # Output — factores (máximo 3, por urgencia)
    topFactors: list[FactorKey]

    # Output — explicaciones detalladas para "Ver por qué" (opcional según feature flag)
    factorExplanations: list[dict] = []

    # Contexto de hábitos
    defaultsUsed: HabitDefaults
    overridesToday: dict = Field(default_factory=dict)


# ─────────────────────────────────────────────
# USER PREFERENCES
# ─────────────────────────────────────────────

class UserPreferences(BaseModel):
    lang: Lang = "es"
    goal: Goal = "health"
    defaults: HabitDefaults = Field(default_factory=HabitDefaults)


# ─────────────────────────────────────────────
# REQUEST BODIES
# ─────────────────────────────────────────────

class ComputeRequest(BaseModel):
    snapshot: GarminSnapshot
    habits: Optional[HabitOverride] = None
    lang: Lang = "es"


class DefaultsPatchRequest(BaseModel):
    caffeineLate: Optional[CaffeineLate] = None
    alcohol: Optional[Alcohol] = None
    lateDinner: Optional[LateDinner] = None


class OverridePutRequest(BaseModel):
    caffeineLate: Optional[CaffeineLate] = None
    alcohol: Optional[Alcohol] = None
    lateDinner: Optional[LateDinner] = None
    energyManual: Optional[int] = None


# ─────────────────────────────────────────────
# API RESPONSE WRAPPER
# ─────────────────────────────────────────────

class ApiError(BaseModel):
    code: str
    message: str


class ApiResponse(BaseModel):
    data: Optional[dict] = None
    error: Optional[ApiError] = None
