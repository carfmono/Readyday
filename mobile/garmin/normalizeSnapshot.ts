/**
 * ReadyDay — Snapshot Normalizer (TypeScript)
 * Puerto exacto de backend/normalize_snapshot.py
 * Se ejecuta en mobile/domain antes de pasar datos al scoreEngine.
 *
 * Mismos defaults, mismos rangos, misma lógica de clamping.
 * Mismos umbrales de confidence.
 */

import type { GarminSnapshot, FactorKey } from '../../shared-types/readiness';

// ─────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────

/** Snapshot con todos los campos garantizados (no null) + metadatos de limpieza */
export type CleanSnapshot = {
  capturedAt: string;
  bodyBattery: number;
  sleepScore: number;
  sleepHours: number;
  hrResting: number;
  stressAvg: number;
  activityLoad: number;
  recoveryTimeH: number;
  /** Campos que vinieron null — usados para calcular confidenceScore */
  _nullFields: string[];
};

// ─────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────

type MetricKey = keyof Omit<GarminSnapshot, 'capturedAt'>;

const DEFAULTS: Record<MetricKey, number> = {
  bodyBattery:   50,
  sleepScore:    50,
  sleepHours:    7.0,
  hrResting:     65,
  stressAvg:     50,
  activityLoad:  0,
  recoveryTimeH: 0,
};

const RANGES: Record<MetricKey, [number, number]> = {
  bodyBattery:   [0,    100],
  sleepScore:    [0,    100],
  sleepHours:    [0,     24],
  hrResting:     [30,   220],
  stressAvg:     [0,    100],
  activityLoad:  [0,    100],
  recoveryTimeH: [0,    168],
};

const KEY_METRICS:       MetricKey[] = ['bodyBattery', 'sleepScore', 'hrResting'];
const SECONDARY_METRICS: MetricKey[] = ['sleepHours', 'stressAvg', 'activityLoad', 'recoveryTimeH'];
const ALL_METRICS:       MetricKey[] = [...KEY_METRICS, ...SECONDARY_METRICS];

// ─────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────

function clamp(v: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, v));
}

// ─────────────────────────────────────────────
// NORMALIZACIÓN
// ─────────────────────────────────────────────

/**
 * Convierte un GarminSnapshot crudo en un CleanSnapshot normalizado.
 * Puerto directo de normalize_snapshot() en Python.
 *
 * - null/undefined → default razonable
 * - fuera de rango → clampeado al límite
 * - todo convertido a number
 */
export function normalizeSnapshot(raw: GarminSnapshot): CleanSnapshot {
  const nullFields: string[] = [];
  const clean: Record<string, unknown> = { capturedAt: raw.capturedAt };

  for (const key of ALL_METRICS) {
    const rawVal = raw[key];

    if (rawVal === null || rawVal === undefined) {
      clean[key] = DEFAULTS[key];
      nullFields.push(key);
    } else {
      const [lo, hi] = RANGES[key];
      const v = Number(rawVal);
      clean[key] = isNaN(v) ? DEFAULTS[key] : clamp(v, lo, hi);
      if (isNaN(v)) nullFields.push(key);
    }
  }

  return {
    ...(clean as Omit<CleanSnapshot, '_nullFields'>),
    _nullFields: nullFields,
  };
}

// ─────────────────────────────────────────────
// CONFIDENCE SCORE
// ─────────────────────────────────────────────

/**
 * Calcula qué tan confiables son los datos de entrada (0-100).
 * Puerto de calculate_confidence() en Python.
 * Mismos umbrales — mismo resultado para el mismo input.
 */
export function calculateConfidence(raw: GarminSnapshot): number {
  const missingKey = KEY_METRICS.filter(m => raw[m] === null || raw[m] === undefined).length;
  const missingSec = SECONDARY_METRICS.filter(m => raw[m] === null || raw[m] === undefined).length;

  if (missingKey === 0 && missingSec === 0) return 95;
  if (missingKey === 0 && missingSec === 1) return 80;
  if (missingKey === 0 && missingSec === 2) return 70;
  if (missingKey === 0)                     return 60;
  if (missingKey === 1)                     return 55;
  if (missingKey === 2)                     return 35;
  return 20;
}

/**
 * Devuelve los nombres de los campos que vinieron null en el snapshot.
 */
export function getNullFields(raw: GarminSnapshot): string[] {
  return ALL_METRICS.filter(m => raw[m] === null || raw[m] === undefined);
}
