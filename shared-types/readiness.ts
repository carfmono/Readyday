/**
 * ReadyDay — Contrato de datos central V2
 * Fuente de verdad compartida entre backend, mobile y garmin bridge.
 * No importa de ninguna capa concreta.
 */

export type Zone = 'green' | 'yellow' | 'red';

export type FactorKey = 'bb' | 'sleep' | 'stress' | 'hr' | 'act' | 'rt' | 'habits';

/**
 * Explicación legible de un factor para el modal "Ver por qué".
 * Generado por explanation_engine.py / explanationEngine.ts
 */
export type FactorExplanation = {
  key: FactorKey;
  impact: 'positive' | 'negative';
  text: string;
};

export type HabitDefaults = {
  caffeineLate: { cups: number; lastTime: string | null };
  alcohol: { drinks: number };
  lateDinner: { ate: boolean; time: string | null };
};

export type HabitOverride = HabitDefaults & {
  energyManual: number | null; // 0-4 (Muy baja→Muy alta pill index)
};

/**
 * Snapshot de datos crudos desde Garmin (o mock).
 * Todos los campos son nullable porque Garmin puede no tenerlos disponibles.
 */
export type GarminSnapshot = {
  capturedAt: string;           // ISO datetime
  bodyBattery: number | null;   // 0-100
  sleepScore: number | null;    // 0-100
  sleepHours: number | null;    // decimal hours
  hrResting: number | null;     // bpm
  stressAvg: number | null;     // 0-100
  activityLoad: number | null;  // 0-100
  recoveryTimeH: number | null; // hours
};

/**
 * Objeto calculado diario — resultado del motor de scoring.
 * Generado por score_engine.py (backend) y scoreEngine.ts (mobile/domain).
 */
export type DailyReadiness = {
  date: string;                    // ISO date: "2026-04-22"

  // Input — datos Garmin (nullable, se pasan tal cual desde el snapshot)
  bodyBattery: number | null;
  sleepScore: number | null;
  sleepHours: number | null;
  hrResting: number | null;
  stressAvg: number | null;
  activityLoad: number | null;
  recoveryTimeH: number | null;

  // Output — scores calculados (siempre presentes, nunca null)
  recoveryScore: number;           // 0-100
  strainScore: number;             // 0-100
  balanceScore: number;            // puede ser negativo
  zone: Zone;

  // Output — confianza del cálculo (0-100)
  // 95  = todos los datos Garmin presentes
  // 80  = falta 1 métrica secundaria
  // 70  = faltan 2 métricas secundarias
  // 55  = falta 1 métrica clave (bodyBattery, sleepScore, hrResting)
  // ≤35 = faltan 2+ métricas clave
  confidenceScore: number;

  // Output — decisión corta (recommendation_engine)
  recommendation: string;          // "Hoy entrena moderado"

  // Output — explicación y predicción (explanation_engine)
  insight: string;                 // "Estás listo para avanzar, pero..."
  prediction?: string;             // opcional — controlado por FEATURE_PREDICTION

  // Output — factores ordenados por urgencia (máx 3)
  topFactors: FactorKey[];

  // Output — detalle de cada factor (opcional — FEATURE_FACTOR_EXPLANATIONS)
  factorExplanations?: FactorExplanation[];

  // Contexto de hábitos usado para el cálculo
  defaultsUsed: HabitDefaults;
  overridesToday: Partial<HabitOverride>;
};

/**
 * Perfil de usuario — preferencias persistentes
 */
export type UserPreferences = {
  lang: 'es' | 'en';
  goal: 'health' | 'performance' | 'longevity';
  defaults: HabitDefaults;
};

/**
 * Respuesta estándar de la API
 */
export type ApiResponse<T> = {
  data: T;
  error: null;
} | {
  data: null;
  error: { code: string; message: string };
};
