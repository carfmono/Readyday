/**
 * ReadyDay — Garmin Mock Provider
 * Implementa GarminMetricsProvider con datos fijos — idénticos a H[] del HTML MVP.
 *
 * Usar durante Sprint 2 (desarrollo) y Sprint 3 (tests).
 * Reemplazar por garminConnectIQ.ts en Sprint 4 — la interfaz no cambia.
 */

import type { GarminSnapshot } from '../../shared-types/readiness';
import type { GarminMetricsProvider } from './garminAdapter';

// ─────────────────────────────────────────────
// MOCK DATA — puerto del array H[] de index.html
// 7 días de datos representativos que cubren los tres estados del sistema
// ─────────────────────────────────────────────

function dAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10) + 'T07:00:00Z';
}

export const MOCK_HISTORY: GarminSnapshot[] = [
  // Día -6: red — carga alta, sueño pobre
  {
    capturedAt:    dAgo(6),
    bodyBattery:   38,
    stressAvg:     68,
    hrResting:     62,
    sleepScore:    50,
    sleepHours:    5.8,
    activityLoad:  82,
    recoveryTimeH: 52,
  },
  // Día -5: yellow — recuperación parcial
  {
    capturedAt:    dAgo(5),
    bodyBattery:   52,
    stressAvg:     55,
    hrResting:     60,
    sleepScore:    65,
    sleepHours:    6.8,
    activityLoad:  45,
    recoveryTimeH: 38,
  },
  // Día -4: yellow/green — mejorando
  {
    capturedAt:    dAgo(4),
    bodyBattery:   71,
    stressAvg:     42,
    hrResting:     58,
    sleepScore:    78,
    sleepHours:    7.5,
    activityLoad:  30,
    recoveryTimeH: 22,
  },
  // Día -3: green — óptimo
  {
    capturedAt:    dAgo(3),
    bodyBattery:   83,
    stressAvg:     35,
    hrResting:     56,
    sleepScore:    85,
    sleepHours:    7.9,
    activityLoad:  20,
    recoveryTimeH: 14,
  },
  // Día -2: red — alcohol + cena tarde lo hunden
  {
    capturedAt:    dAgo(2),
    bodyBattery:   55,
    stressAvg:     72,
    hrResting:     64,
    sleepScore:    58,
    sleepHours:    6.1,
    activityLoad:  75,
    recoveryTimeH: 36,
  },
  // Día -1: red — cafeína tardía + carga acumulada
  {
    capturedAt:    dAgo(1),
    bodyBattery:   43,
    stressAvg:     62,
    hrResting:     63,
    sleepScore:    55,
    sleepHours:    6.4,
    activityLoad:  68,
    recoveryTimeH: 48,
  },
  // Hoy: yellow — recuperándose, buena noche
  {
    capturedAt:    dAgo(0),
    bodyBattery:   67,
    stressAvg:     45,
    hrResting:     59,
    sleepScore:    74,
    sleepHours:    7.2,
    activityLoad:  40,
    recoveryTimeH: 28,
  },
];

// ─────────────────────────────────────────────
// MOCK HABITS — correlacionados con H[] del HTML MVP
// ─────────────────────────────────────────────

export const MOCK_HABITS_HISTORY = [
  { caffeineLate: { cups: 1, lastTime: '16:00' }, alcohol: { drinks: 0 }, lateDinner: { ate: false, time: null } },
  { caffeineLate: { cups: 0, lastTime: null },    alcohol: { drinks: 0 }, lateDinner: { ate: false, time: null } },
  { caffeineLate: { cups: 0, lastTime: null },    alcohol: { drinks: 0 }, lateDinner: { ate: false, time: null } },
  { caffeineLate: { cups: 0, lastTime: null },    alcohol: { drinks: 0 }, lateDinner: { ate: false, time: null } },
  { caffeineLate: { cups: 0, lastTime: null },    alcohol: { drinks: 2 }, lateDinner: { ate: true, time: '23:00+' } },
  { caffeineLate: { cups: 3, lastTime: '18:00' }, alcohol: { drinks: 0 }, lateDinner: { ate: false, time: null } },
  { caffeineLate: { cups: 0, lastTime: null },    alcohol: { drinks: 0 }, lateDinner: { ate: false, time: null } },
];

// ─────────────────────────────────────────────
// IMPLEMENTACIÓN
// ─────────────────────────────────────────────

export class GarminMockProvider implements GarminMetricsProvider {
  private readonly history: GarminSnapshot[];
  private readonly latencyMs: number;

  /**
   * @param history  Array de snapshots (default: MOCK_HISTORY)
   * @param latencyMs Latencia simulada en ms para imitar async real (default: 80ms)
   */
  constructor(history: GarminSnapshot[] = MOCK_HISTORY, latencyMs = 80) {
    this.history  = history;
    this.latencyMs = latencyMs;
  }

  /** Devuelve el snapshot más reciente (último elemento del array) */
  async getSnapshot(): Promise<GarminSnapshot> {
    await delay(this.latencyMs);
    return this.history[this.history.length - 1];
  }

  /** El mock siempre está disponible */
  isAvailable(): boolean {
    return true;
  }

  /** Utilidad para tests: devuelve el snapshot de hace N días */
  getSnapshotDaysAgo(n: number): GarminSnapshot | undefined {
    return this.history[this.history.length - 1 - n];
  }

  /** Devuelve los últimos N snapshots (para trends) */
  getHistory(days: number = 7): GarminSnapshot[] {
    return this.history.slice(-days);
  }
}

// ─────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ─────────────────────────────────────────────
// SINGLETON DEFAULT — listo para usar en dev
// ─────────────────────────────────────────────

export const garminMock = new GarminMockProvider();
