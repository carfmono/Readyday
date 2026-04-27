/**
 * ReadyDay — API Service
 * Capa de comunicación con el backend FastAPI.
 * Sin lógica de negocio — solo fetch y tipado.
 */

import type { DailyReadiness, ApiResponse } from '../../shared-types/readiness';

const API_BASE = (
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000'
).replace(/\/$/, '');

// ─────────────────────────────────────────────
// TODAY
// ─────────────────────────────────────────────

export async function fetchToday(lang: 'es' | 'en' = 'es'): Promise<DailyReadiness> {
  const res = await fetch(`${API_BASE}/scores/today?lang=${lang}`, {
    headers: { 'Accept': 'application/json' },
  });

  if (!res.ok) {
    throw new Error(`Error del servidor (${res.status})`);
  }

  const json: ApiResponse<DailyReadiness> = await res.json();

  if (json.error) {
    throw new Error(json.error.message);
  }

  if (!json.data) {
    throw new Error('Respuesta vacía del servidor');
  }

  return json.data;
}

// ─────────────────────────────────────────────
// HISTORY (para Trends — Sprint 3)
// ─────────────────────────────────────────────

export async function fetchHistory(days = 7): Promise<DailyReadiness[]> {
  const res = await fetch(`${API_BASE}/scores/history?days=${days}`, {
    headers: { 'Accept': 'application/json' },
  });

  if (!res.ok) throw new Error(`Error del servidor (${res.status})`);

  const json: ApiResponse<DailyReadiness[]> = await res.json();
  if (json.error) throw new Error(json.error.message);
  return json.data ?? [];
}

// ─────────────────────────────────────────────
// HEALTH CHECK
// ─────────────────────────────────────────────

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
    return res.ok;
  } catch {
    return false;
  }
}
