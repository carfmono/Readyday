"""
ReadyDay — Parity Tests (Python)
Lee shared-types/test-fixtures/readiness_cases.json y verifica que
el score engine Python produce exactamente los valores esperados.

En Sprint 5 se añadirá el script de validación JS/TS que usa los mismos fixtures.
Objetivo: JS / Python / TypeScript → mismo input → mismo output.

Ejecutar:
    cd backend && python -m pytest tests/ -v
"""

import json
import sys
from pathlib import Path

import pytest

# Asegurar que los módulos del backend están en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

from score_engine import (
    calculate_recovery,
    calculate_strain,
    calculate_balance,
    get_zone,
    compute_daily_readiness,
    hr_score,
    hab_penalty,
)
from normalize_snapshot import normalize_snapshot, calculate_confidence
from explanation_engine import get_top_factors, explain
from recommendation_engine import get_recommendation

FIXTURES_PATH = (
    Path(__file__).parent.parent.parent
    / "shared-types"
    / "test-fixtures"
    / "readiness_cases.json"
)


def load_cases() -> list[dict]:
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# PARIDAD DE SCORES (test principal)
# Mismos inputs → mismos outputs en todos los environments
# ─────────────────────────────────────────────

@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
def test_score_parity(case: dict) -> None:
    """Verifica que Python produce los scores exactos definidos en los fixtures."""
    snap     = case["snapshot"]
    habits   = case.get("habits", {})
    expected = case["expected"]

    result = compute_daily_readiness(snap, habits)

    assert result["recoveryScore"] == expected["recoveryScore"], (
        f"[{case['id']}] recoveryScore: got {result['recoveryScore']}, "
        f"expected {expected['recoveryScore']}"
    )
    assert result["strainScore"] == expected["strainScore"], (
        f"[{case['id']}] strainScore: got {result['strainScore']}, "
        f"expected {expected['strainScore']}"
    )
    assert result["balanceScore"] == expected["balanceScore"], (
        f"[{case['id']}] balanceScore: got {result['balanceScore']}, "
        f"expected {expected['balanceScore']}"
    )
    assert result["zone"] == expected["zone"], (
        f"[{case['id']}] zone: got '{result['zone']}', "
        f"expected '{expected['zone']}'"
    )


# ─────────────────────────────────────────────
# TESTS UNITARIOS — funciones core
# ─────────────────────────────────────────────

class TestHrScore:
    def test_elite(self):     assert hr_score(48) == 100
    def test_boundary_50(self):  assert hr_score(50) == 100
    def test_boundary_55(self):  assert hr_score(55) == 90
    def test_boundary_60(self):  assert hr_score(60) == 75
    def test_boundary_65(self):  assert hr_score(65) == 55
    def test_boundary_70(self):  assert hr_score(70) == 35
    def test_high(self):      assert hr_score(80) == 20
    def test_above_70(self):  assert hr_score(71) == 20


class TestHabPenalty:
    def test_no_habits(self):
        assert hab_penalty({}) == 0

    def test_caffeine_only(self):
        h = {"caffeineLate": {"cups": 2}}
        assert hab_penalty(h) == 16      # 2*8 = 16

    def test_caffeine_cap(self):
        h = {"caffeineLate": {"cups": 10}}
        assert hab_penalty(h) == 28      # capped at 28

    def test_alcohol_only(self):
        h = {"alcohol": {"drinks": 1}}
        assert hab_penalty(h) == 13

    def test_alcohol_cap(self):
        h = {"alcohol": {"drinks": 10}}
        assert hab_penalty(h) == 35      # capped at 35

    def test_late_dinner_23(self):
        h = {"lateDinner": {"ate": True, "time": "23:00+"}}
        assert hab_penalty(h) == 20

    def test_late_dinner_22(self):
        h = {"lateDinner": {"ate": True, "time": "22:00"}}
        assert hab_penalty(h) == 13

    def test_late_dinner_early(self):
        h = {"lateDinner": {"ate": True, "time": "21:00"}}
        assert hab_penalty(h) == 7

    def test_no_dinner(self):
        h = {"lateDinner": {"ate": False, "time": None}}
        assert hab_penalty(h) == 0

    def test_combined_max(self):
        # 28 + 35 + 20 = 83 — por debajo del cap de 100
        h = {
            "caffeineLate": {"cups": 10},
            "alcohol": {"drinks": 10},
            "lateDinner": {"ate": True, "time": "23:00+"},
        }
        assert hab_penalty(h) == 83

    def test_combined_at_100(self):
        h = {
            "caffeineLate": {"cups": 10},
            "alcohol": {"drinks": 10},
            "lateDinner": {"ate": True, "time": "23:00+"},
        }
        # 28 + 35 + 20 = 83 < 100 — so result is 83
        assert hab_penalty(h) == 83


class TestGetZone:
    def test_green(self):   assert get_zone(70, 20) == "green"
    def test_green_high(self): assert get_zone(100, 100) == "green"
    def test_yellow_rec(self): assert get_zone(45, 10) == "yellow"   # rec>=45 but bal<20
    def test_yellow_bal(self): assert get_zone(69, 19) == "yellow"   # rec<70 or bal<20
    def test_red(self):     assert get_zone(44, 50) == "red"          # rec<45
    def test_red_negative(self): assert get_zone(30, -10) == "red"


class TestCalculateBalance:
    def test_basic(self):    assert calculate_balance(67, 36) == 49
    def test_negative(self): assert calculate_balance(23, 71) == -13
    def test_zero(self):     assert calculate_balance(50, 50) == 25  # 50 - round(25) = 25


# ─────────────────────────────────────────────
# TESTS DE NORMALIZACIÓN
# ─────────────────────────────────────────────

class TestNormalizeSnapshot:
    def test_all_present(self):
        snap = {
            "capturedAt": "2026-04-22T07:00:00Z",
            "bodyBattery": 70, "sleepScore": 80, "sleepHours": 7.5,
            "hrResting": 58, "stressAvg": 40, "activityLoad": 30, "recoveryTimeH": 12,
        }
        clean = normalize_snapshot(snap)
        assert clean["bodyBattery"] == 70.0
        assert clean["_nullFields"] == []

    def test_null_defaults(self):
        snap = {"capturedAt": "2026-04-22T07:00:00Z", "bodyBattery": None}
        clean = normalize_snapshot(snap)
        assert clean["bodyBattery"] == 50.0   # default
        assert "bodyBattery" in clean["_nullFields"]

    def test_clamping(self):
        snap = {"capturedAt": "2026-04-22T07:00:00Z", "bodyBattery": 150, "stressAvg": -10}
        clean = normalize_snapshot(snap)
        assert clean["bodyBattery"] == 100.0
        assert clean["stressAvg"] == 0.0


class TestCalculateConfidence:
    def test_all_present(self):
        snap = {
            "bodyBattery": 70, "sleepScore": 80, "hrResting": 58,
            "sleepHours": 7.5, "stressAvg": 40, "activityLoad": 30, "recoveryTimeH": 12,
        }
        assert calculate_confidence(snap) == 95

    def test_missing_one_secondary(self):
        snap = {"bodyBattery": 70, "sleepScore": 80, "hrResting": 58,
                "stressAvg": 40, "activityLoad": 30, "recoveryTimeH": 12}
        # sleepHours missing
        assert calculate_confidence(snap) == 80

    def test_missing_key_metric(self):
        snap = {"sleepScore": 80, "hrResting": 58,
                "sleepHours": 7.5, "stressAvg": 40, "activityLoad": 30, "recoveryTimeH": 12}
        # bodyBattery missing
        assert calculate_confidence(snap) == 55

    def test_all_missing(self):
        assert calculate_confidence({}) == 20


# ─────────────────────────────────────────────
# TESTS DE EXPLANATION ENGINE
# ─────────────────────────────────────────────

class TestGetTopFactors:
    def test_returns_max_3(self):
        snap = {"bodyBattery": 20, "sleepScore": 30, "stressAvg": 80,
                "hrResting": 75, "activityLoad": 90, "recoveryTimeH": 50}
        factors = get_top_factors(snap, {}, max_n=3)
        assert len(factors) == 3

    def test_bb_urgent_when_low(self):
        snap = {"bodyBattery": 5, "sleepScore": 80, "stressAvg": 20,
                "hrResting": 50, "activityLoad": 10, "recoveryTimeH": 2}
        factors = get_top_factors(snap)
        assert factors[0] == "bb"

    def test_stress_urgent_when_high(self):
        snap = {"bodyBattery": 80, "sleepScore": 80, "stressAvg": 95,
                "hrResting": 50, "activityLoad": 0, "recoveryTimeH": 0}
        factors = get_top_factors(snap)
        assert factors[0] == "stress"


class TestRecommendation:
    def test_green(self):
        snap = {"activityLoad": 20}
        assert get_recommendation("green", snap, "es") == "Hoy entrena fuerte"
        assert get_recommendation("green", snap, "en") == "Train hard today"

    def test_yellow_moderate(self):
        snap = {"activityLoad": 30}
        assert get_recommendation("yellow", snap, "es") == "Hoy entrena moderado"

    def test_yellow_light_high_activity(self):
        snap = {"activityLoad": 75}
        assert get_recommendation("yellow", snap, "es") == "Hoy entrena suave"

    def test_red(self):
        snap = {"activityLoad": 0}
        assert get_recommendation("red", snap, "es") == "Hoy descansa"
        assert get_recommendation("red", snap, "en") == "Rest today"
