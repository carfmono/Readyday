/**
 * ReadyDay — Explanation Engine (TypeScript)
 * Puerto de backend/explanation_engine.py
 * Responsabilidad: topFactors, insight, prediction, factorExplanations.
 *
 * Funciones puras — sin side effects.
 */

import type { Zone, FactorKey, FactorExplanation, HabitDefaults } from '../../shared-types/readiness';
import type { CleanSnapshot } from '../garmin/normalizeSnapshot';
import { habPenalty } from './scoreEngine';

export type Lang = 'es' | 'en';

type Habits = Partial<HabitDefaults>;

// ─────────────────────────────────────────────
// TOP FACTORS
// ─────────────────────────────────────────────

/**
 * Devuelve los factores más urgentes (más alejados del óptimo).
 * Puerto del urgency sort de renderToday() del HTML MVP.
 * Incluye 'habits' como factor cuando la penalización es alta.
 */
export function getTopFactors(
  snap: CleanSnapshot,
  habits: Habits = {},
  maxN: number = 3
): FactorKey[] {
  const hp = habPenalty(habits);

  const urgency: Record<FactorKey, number> = {
    bb:     100 - snap.bodyBattery,
    sleep:  100 - snap.sleepScore,
    stress: snap.stressAvg,
    hr:     Math.max(0, (snap.hrResting - 55) * 3),
    act:    snap.activityLoad,
    rt:     Math.min(snap.recoveryTimeH * 2, 100),
    habits: hp,
  };

  return (Object.entries(urgency) as [FactorKey, number][])
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxN)
    .map(([key]) => key);
}

// ─────────────────────────────────────────────
// INSIGHT
// ─────────────────────────────────────────────

/**
 * Texto de insight contextual.
 * Puerto de get_insight() de Python — misma lógica de ramas.
 */
export function getInsight(
  zone: Zone,
  snap: CleanSnapshot,
  habits: Habits = {},
  lang: Lang = 'es'
): string {
  const e = lang === 'es';

  const cups   = habits.caffeineLate?.cups ?? 0;
  const drinks = habits.alcohol?.drinks ?? 0;

  if (zone === 'green') {
    return e
      ? 'Tus reservas están altas y el estrés bajo control. Es un buen día para dar el máximo.'
      : "Reserves are high and stress is under control. A good day to give your best.";
  }

  if (zone === 'yellow') {
    if (snap.sleepScore < 60) {
      return e
        ? 'Tu recuperación aún no es completa. Evita alta intensidad hoy. ⚠️'
        : "Your recovery isn't complete yet. Avoid high intensity today. ⚠️";
    }
    if (cups > 2) {
      return e
        ? 'La cafeína tardía afectó tu sueño. Moderado es lo correcto hoy.'
        : 'Late caffeine affected your sleep. Moderate effort is right today.';
    }
    if (drinks > 0) {
      return e
        ? 'El alcohol de ayer redujo tu recuperación nocturna. Ve con cuidado.'
        : "Last night's alcohol reduced your overnight recovery. Take it easy.";
    }
    return e
      ? 'Estás listo para avanzar, pero no para exigirte al máximo.'
      : "You're ready to move forward, but not to push to the limit.";
  }

  // red
  if (snap.bodyBattery < 30) {
    return e
      ? 'Batería muy baja. El descanso de hoy es la mejor inversión para mañana.'
      : "Battery very low. Today's rest is the best investment for tomorrow.";
  }
  return e
    ? 'Tu cuerpo necesita recuperarse. Forzar hoy puede costarte varios días.'
    : 'Your body needs to recover. Pushing today could cost you several days.';
}

// ─────────────────────────────────────────────
// PREDICTION
// ─────────────────────────────────────────────

/**
 * Texto de predicción.
 * Puerto de get_prediction() de Python.
 */
export function getPrediction(zone: Zone, lang: Lang = 'es'): string {
  const e = lang === 'es';

  if (zone === 'green') {
    return e
      ? 'Si entrenas fuerte hoy → mañana las reservas bajarán, pero habrás invertido en rendimiento real.'
      : "Train hard today → tomorrow reserves drop, but you'll have invested in real performance.";
  }
  if (zone === 'yellow') {
    return e
      ? 'Si entrenas moderado hoy → mañana podrías mejorar tu recuperación +8 a +12 pts.'
      : 'Train moderate today → tomorrow your recovery could improve +8 to +12 pts.';
  }
  return e
    ? 'Si descansas hoy → mañana podrías recuperar entre +10 y +18 puntos.'
    : 'Rest today → tomorrow you could recover +10 to +18 points.';
}

// ─────────────────────────────────────────────
// FACTOR EXPLANATIONS
// ─────────────────────────────────────────────

/**
 * Genera explicaciones para el modal "Ver por qué".
 * Formato V2: { key, impact, text }
 */
export function getFactorExplanations(
  topFactors: FactorKey[],
  snap: CleanSnapshot,
  habits: Habits = {},
  lang: Lang = 'es'
): FactorExplanation[] {
  const e = lang === 'es';
  const result: FactorExplanation[] = [];

  for (const key of topFactors) {
    let text = '';

    switch (key) {
      case 'bb': {
        const v = snap.bodyBattery;
        text = e
          ? `Body Battery en ${v}/100. ${v < 40 ? 'Nivel bajo — el cuerpo aún procesa el esfuerzo reciente.' : 'Nivel moderado — no está al tope, hay margen de mejora.'}`
          : `Body Battery at ${v}/100. ${v < 40 ? 'Low — your body is still processing recent effort.' : 'Moderate — not at full, room to improve.'}`;
        break;
      }
      case 'sleep': {
        const v = snap.sleepScore;
        text = e
          ? `Score de sueño: ${v}/100. ${v < 60 ? 'Sueño insuficiente — la recuperación nocturna no fue completa.' : 'Sueño aceptable pero con margen de mejora.'}`
          : `Sleep score: ${v}/100. ${v < 60 ? "Insufficient — overnight recovery wasn't complete." : 'Acceptable but room to improve.'}`;
        break;
      }
      case 'stress': {
        const v = snap.stressAvg;
        text = e
          ? `Estrés promedio de ayer: ${v}/100. ${v > 60 ? 'Nivel elevado — el sistema nervioso necesita calma.' : 'Nivel moderado — manejable pero presente.'}`
          : `Average stress yesterday: ${v}/100. ${v > 60 ? 'High — the nervous system needs calm.' : 'Moderate — manageable but present.'}`;
        break;
      }
      case 'hr': {
        const v = snap.hrResting;
        text = e
          ? `FC en reposo: ${v} bpm. ${v > 65 ? 'Alta — señal de carga acumulada o recuperación incompleta.' : 'Ligeramente elevada — el corazón aún no está en su mejor punto.'}`
          : `Resting HR: ${v} bpm. ${v > 65 ? 'High — sign of accumulated load or incomplete recovery.' : "Slightly elevated — heart isn't at its best yet."}`;
        break;
      }
      case 'act': {
        const v = snap.activityLoad;
        text = e
          ? `Carga de actividad: ${v}/100. ${v > 60 ? 'Alta — el cuerpo aún digiere el entrenamiento reciente.' : 'Moderada — presente pero manejable.'}`
          : `Activity load: ${v}/100. ${v > 60 ? 'High — your body is still digesting recent training.' : 'Moderate — present but manageable.'}`;
        break;
      }
      case 'rt': {
        const v = snap.recoveryTimeH;
        text = e
          ? `Tiempo estimado de recuperación: ${v}h. ${v > 24 ? 'Necesitas más descanso antes de volver a exigirte al máximo.' : 'Casi listo — pocas horas más completarán la recuperación.'}`
          : `Estimated recovery time: ${v}h. ${v > 24 ? 'You need more rest before pushing hard again.' : 'Almost there — a few more hours will complete recovery.'}`;
        break;
      }
      case 'habits': {
        const hp = habPenalty(habits);
        const parts: string[] = [];
        if (habits.caffeineLate?.cups) parts.push(e ? `${habits.caffeineLate.cups} café${habits.caffeineLate.cups > 1 ? 's' : ''} tarde` : `${habits.caffeineLate.cups} late coffee${habits.caffeineLate.cups > 1 ? 's' : ''}`);
        if (habits.alcohol?.drinks)    parts.push(e ? `${habits.alcohol.drinks} bebida${habits.alcohol.drinks > 1 ? 's' : ''} alcohólica${habits.alcohol.drinks > 1 ? 's' : ''}` : `${habits.alcohol.drinks} alcoholic drink${habits.alcohol.drinks > 1 ? 's' : ''}`);
        if (habits.lateDinner?.ate)    parts.push(e ? 'cena tarde' : 'late dinner');
        const causes = parts.length ? parts.join(', ') : (e ? 'varios factores' : 'various factors');
        text = e
          ? `Impacto de hábitos: -${hp} pts. Factores: ${causes}.`
          : `Habit impact: -${hp} pts. Factors: ${causes}.`;
        break;
      }
    }

    if (text) {
      result.push({ key, impact: 'negative', text });
    }
  }

  return result;
}

// ─────────────────────────────────────────────
// EXPLAIN — función principal
// ─────────────────────────────────────────────

export type ExplainResult = {
  topFactors: FactorKey[];
  insight: string;
  prediction: string;
  factorExplanations: FactorExplanation[];
};

/**
 * Función principal — genera todo el contenido explicativo.
 * Llamar después de computeScores().
 */
export function explain(
  zone: Zone,
  snap: CleanSnapshot,
  habits: Habits = {},
  lang: Lang = 'es',
  maxFactors: number = 3,
): ExplainResult {
  const topFactors = getTopFactors(snap, habits, maxFactors);

  return {
    topFactors,
    insight:            getInsight(zone, snap, habits, lang),
    prediction:         getPrediction(zone, lang),
    factorExplanations: getFactorExplanations(topFactors, snap, habits, lang),
  };
}
