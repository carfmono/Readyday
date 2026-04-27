/**
 * ReadyDay — FactorsList (refined)
 *
 * "POR QUÉ" — explica los factores detrás del score.
 * Icono en píldora con fondo suave · texto hasta 3 líneas.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { FactorKey, FactorExplanation } from '../../shared-types/readiness';
import { Colors } from '../constants/colors';

// ─────────────────────────────────────────────
// METADATA LOCAL
// ─────────────────────────────────────────────

const FACTOR_META: Record<FactorKey, { icon: string; label: string; color: string }> = {
  bb:     { icon: '⚡', label: 'Body Battery',      color: 'rgba(124,110,255,0.15)' },
  sleep:  { icon: '😴', label: 'Sueño',             color: 'rgba(90,160,255,0.15)'  },
  stress: { icon: '🧠', label: 'Estrés',            color: 'rgba(255,100,100,0.15)' },
  hr:     { icon: '❤️', label: 'FC en reposo',      color: 'rgba(255,80,100,0.15)'  },
  act:    { icon: '🔥', label: 'Carga activa',      color: 'rgba(255,140,60,0.15)'  },
  rt:     { icon: '⏱️', label: 'T. Recuperación',  color: 'rgba(60,220,140,0.15)'  },
  habits: { icon: '🌙', label: 'Hábitos',           color: 'rgba(255,200,80,0.15)'  },
};

// ─────────────────────────────────────────────
// COMPONENTE
// ─────────────────────────────────────────────

interface Props {
  topFactors: FactorKey[];
  factorExplanations?: FactorExplanation[];
}

export function FactorsList({ topFactors, factorExplanations = [] }: Props) {
  if (topFactors.length === 0) return null;

  return (
    <View style={styles.section}>
      <Text style={styles.title}>POR QUÉ</Text>
      {topFactors.map((key) => {
        const meta = FACTOR_META[key] ?? { icon: '•', label: key, color: 'rgba(255,255,255,0.08)' };
        const explanation = factorExplanations.find((e) => e.key === key);

        return (
          <FactorRow
            key={key}
            icon={meta.icon}
            iconBg={meta.color}
            label={meta.label}
            text={explanation?.text}
          />
        );
      })}
    </View>
  );
}

// ─────────────────────────────────────────────
// FACTOR ROW
// ─────────────────────────────────────────────

interface RowProps {
  icon: string;
  iconBg: string;
  label: string;
  text?: string;
}

function FactorRow({ icon, iconBg, label, text }: RowProps) {
  return (
    <View style={styles.row}>
      <View style={[styles.iconWrap, { backgroundColor: iconBg }]}>
        <Text style={styles.icon}>{icon}</Text>
      </View>
      <View style={styles.rowBody}>
        <Text style={styles.rowLabel}>{label}</Text>
        {text && (
          <Text style={styles.rowText} numberOfLines={3}>
            {text}
          </Text>
        )}
      </View>
    </View>
  );
}

// ─────────────────────────────────────────────
// STYLES
// ─────────────────────────────────────────────

const styles = StyleSheet.create({
  section: {
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 1.2,
    color: Colors.text3,
    marginBottom: 10,
    marginLeft: 2,
  },

  // Row
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 14,
    marginBottom: 8,
    paddingHorizontal: 14,
    paddingVertical: 13,
    gap: 13,
  },
  iconWrap: {
    width: 38,
    height: 38,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  icon: {
    fontSize: 18,
  },
  rowBody: {
    flex: 1,
    paddingTop: 1,
  },
  rowLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 4,
    letterSpacing: -0.2,
  },
  rowText: {
    fontSize: 12,
    lineHeight: 17,
    color: Colors.text2,
    fontWeight: '500',
  },
});
