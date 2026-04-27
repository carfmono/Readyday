/**
 * ReadyDay — Design tokens
 * Puerto directo de las CSS variables de mvp/index.html.
 */

import type { Zone } from '../../shared-types/readiness';

export const Colors = {
  // Fondos
  bg:      '#07070F',
  bg2:     '#0D0D1A',
  card:    '#121220',
  card2:   '#1A1A2C',

  // Bordes
  border:  'rgba(255,255,255,0.07)',

  // Texto
  text:    '#F0F0FA',
  text2:   '#8888A8',
  text3:   '#4A4A6A',

  // Colores de estado
  purple:  '#7C6EFF',
  green:   '#00D68F',
  yellow:  '#FFCC00',
  red:     '#FF4757',
} as const;

export function zoneColor(zone: Zone): string {
  if (zone === 'green')  return Colors.green;
  if (zone === 'yellow') return Colors.yellow;
  return Colors.red;
}

export function zoneBg(zone: Zone): string {
  if (zone === 'green')  return 'rgba(0,214,143,0.08)';
  if (zone === 'yellow') return 'rgba(255,204,0,0.08)';
  return 'rgba(255,71,87,0.08)';
}

export function zoneName(zone: Zone, lang: 'es' | 'en' = 'es'): string {
  const map = {
    es: { green: 'Óptimo', yellow: 'Moderado', red: 'Recuperación' },
    en: { green: 'Optimal', yellow: 'Moderate', red: 'Recovery' },
  };
  return map[lang][zone];
}
