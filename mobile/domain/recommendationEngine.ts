/**
 * ReadyDay — Recommendation Engine (TypeScript)
 * Puerto de backend/recommendation_engine.py
 * Responsabilidad única: decisión principal (copy corto de acción diaria).
 *
 * Para insight, prediction y topFactors → explanationEngine.ts
 */

import type { Zone } from '../../shared-types/readiness';
import type { CleanSnapshot } from '../garmin/normalizeSnapshot';

export type Lang = 'es' | 'en';

/**
 * Devuelve la decisión corta del día.
 * Puerto de get_recommendation() de Python.
 *
 * "Hoy entrena fuerte" / "Hoy entrena moderado" / "Hoy entrena suave" / "Hoy descansa"
 */
export function getRecommendation(zone: Zone, snap: CleanSnapshot, lang: Lang = 'es'): string {
  const e = lang === 'es';
  const activity = snap.activityLoad;

  if (zone === 'green') return e ? 'Hoy entrena fuerte' : 'Train hard today';
  if (zone === 'yellow') {
    if (activity > 60) return e ? 'Hoy entrena suave' : 'Go light today';
    return e ? 'Hoy entrena moderado' : 'Train moderate today';
  }
  return e ? 'Hoy descansa' : 'Rest today';
}
