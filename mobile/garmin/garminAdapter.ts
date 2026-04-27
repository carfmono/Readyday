/**
 * ReadyDay — Garmin Adapter Interface
 *
 * Interfaz estable que desacopla el Garmin SDK del resto de la app.
 * El domain layer NUNCA importa ConnectIQ SDK directamente — siempre usa esta interfaz.
 *
 * Implementaciones:
 *   - garminMock.ts       → Sprint 2 (mock data para desarrollo)
 *   - garminConnectIQ.ts  → Sprint 4 (SDK real de Garmin Connect IQ)
 */

import type { GarminSnapshot } from '../../shared-types/readiness';

// ─────────────────────────────────────────────
// INTERFAZ PRINCIPAL
// ─────────────────────────────────────────────

/**
 * Contrato que toda implementación Garmin debe satisfacer.
 * Una sola operación: getSnapshot() → devuelve el snapshot del día actual.
 *
 * La granularidad de la llamada (Bluetooth, HTTP, local cache)
 * es responsabilidad de la implementación, no del contrato.
 */
export interface GarminMetricsProvider {
  /**
   * Devuelve el snapshot más reciente de métricas Garmin.
   * Puede lanzar GarminNotAvailableError si el dispositivo no está conectado.
   */
  getSnapshot(): Promise<GarminSnapshot>;

  /**
   * Indica si hay un dispositivo Garmin disponible/conectado.
   * Usar para decidir si mostrar el badge "Datos reales" o "Datos estimados".
   */
  isAvailable(): boolean;
}

// ─────────────────────────────────────────────
// ERROR TYPES
// ─────────────────────────────────────────────

export class GarminNotAvailableError extends Error {
  constructor(reason?: string) {
    super(reason ?? 'Garmin device not available');
    this.name = 'GarminNotAvailableError';
  }
}

export class GarminDataStaleError extends Error {
  constructor(public lastUpdatedAt: string) {
    super(`Garmin data is stale. Last updated: ${lastUpdatedAt}`);
    this.name = 'GarminDataStaleError';
  }
}
