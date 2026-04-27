/**
 * ReadyDay — Score Engine (TypeScript)
 * Puerto directo de backend/score_engine.py
 * Mismos pesos, mismos umbrales, misma lógica.
 * Funciones puras — sin efectos secundarios, sin imports de storage o UI.
 *
 * Paridad garantizada con el backend via shared-types/test-fixtures/readiness_cases.json
 */

import type { Zone, HabitDefaults } from '../../shared-types/readiness';
import type { CleanSnapshot } from '../garmin/normalizeSnapshot';

// ─────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────

export type ScoreResult = {
  recoveryScore: number;
  strainScore: number;
  balanceScore: number;
  zone: Zone;
};

type Habits = Partial<HabitDefaults>;

// ─────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────

function clamp(v: number, a: number, b: number): number {
  return Math.max(a, Math.min(b, v));
}

/**
 * Convierte FC en reposo a score de recuperación (0-100).
 * Puerto de hrScore() del HTML MVP y score_engine.py
 */
export function hrScore(hr: number): number {
  if (hr <= 50) return 100;
  if (hr <= 55) return 90;
  if (hr <= 60) return 75;
  if (hr <= 65) return 55;
  if (hr <= 70) return 35;
  return 20;
}

/**
 * Penalización por hábitos (0-100).
 * Puerto de habPen() del HTML MVP y hab_penalty() de score_engine.py
 * Pesos: café +8/taza (max 28) · alcohol +13/bebida (max 35) · cena 7/13/20
 */
export function habPenalty(habits: Habits): number {
  // Cafeína tardía
  const caffeine = habits.caffeineLate;
  const cups     = caffeine?.cups ?? 0;
  const cPenalty = Math.min(cups * 8, 28);

  // Alcohol
  const alcohol  = habits.alcohol;
  const drinks   = alcohol?.drinks ?? 0;
  const aPenalty = Math.min(drinks * 13, 35);

  // Cena tardía
  const dinner   = habits.lateDinner;
  const ate      = dinner?.ate ?? false;
  const time     = dinner?.time ?? '22:00';
  let dPenalty   = 0;
  if (ate) {
    if (time === '23:00+') dPenalty = 20;
    else if (time === '22:00') dPenalty = 13;
    else dPenalty = 7;
  }

  return Math.min(cPenalty + aPenalty + dPenalty, 100);
}

// ─────────────────────────────────────────────
// SCORE ENGINE CORE
// ─────────────────────────────────────────────

/**
 * Recovery Score (0-100).
 * Fórmula: 0.35×BB + 0.25×(100-Stress) + 0.20×HRscore + 0.20×Sleep
 */
export function calculateRecovery(snap: CleanSnapshot, habits: Habits): number {
  return clamp(
    Math.round(
      0.35 * snap.bodyBattery +
      0.25 * (100 - snap.stressAvg) +
      0.20 * hrScore(snap.hrResting) +
      0.20 * snap.sleepScore
    ),
    0, 100
  );
}

/**
 * Strain Score (0-100).
 * Fórmula: 0.40×ActivityLoad + 0.25×RecoveryTimePenalty + 0.20×Stress + 0.15×HabitPenalty
 *
 * Recovery time penalty:
 *   ≥48h → 85 | ≥36h → 65 | ≥24h → 45 | ≥12h → 25 | else → 10
 */
export function calculateStrain(snap: CleanSnapshot, habits: Habits): number {
  const rt = snap.recoveryTimeH;
  const rtPenalty = rt >= 48 ? 85 : rt >= 36 ? 65 : rt >= 24 ? 45 : rt >= 12 ? 25 : 10;
  const hp = habPenalty(habits);

  return clamp(
    Math.round(
      0.40 * snap.activityLoad +
      0.25 * rtPenalty +
      0.20 * snap.stressAvg +
      0.15 * hp
    ),
    0, 100
  );
}

/**
 * Balance = Recovery - round(Strain / 2)
 */
export function calculateBalance(recovery: number, strain: number): number {
  return recovery - Math.round(strain / 2);
}

/**
 * Zona de readiness.
 * green: rec≥70 AND bal≥20 | yellow: rec≥45 | red: resto
 */
export function getZone(recovery: number, balance: number): Zone {
  if (recovery >= 70 && balance >= 20) return 'green';
  if (recovery >= 45) return 'yellow';
  return 'red';
}

/**
 * Función principal — calcula todos los scores matemáticos.
 * Sin textos, sin factores (→ explanationEngine.ts)
 */
export function computeScores(snap: CleanSnapshot, habits: Habits): ScoreResult {
  const recovery = calculateRecovery(snap, habits);
  const strain   = calculateStrain(snap, habits);
  const balance  = calculateBalance(recovery, strain);
  const zone     = getZone(recovery, balance);

  return { recoveryScore: recovery, strainScore: strain, balanceScore: balance, zone };
}
