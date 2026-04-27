/**
 * ReadyDay — ScoreCard (refined)
 *
 * Jerarquía: Decisión → Número → Desglose
 * La recomendación es el titular. El score es el argumento.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { DailyReadiness } from '../../shared-types/readiness';
import { Colors, zoneColor, zoneBg, zoneName } from '../constants/colors';

interface Props {
  data: Pick<
    DailyReadiness,
    | 'recoveryScore'
    | 'strainScore'
    | 'balanceScore'
    | 'zone'
    | 'recommendation'
    | 'confidenceScore'
  >;
}

export function ScoreCard({ data }: Props) {
  const zc  = zoneColor(data.zone);
  const zbg = zoneBg(data.zone);
  const zn  = zoneName(data.zone);

  return (
    <View style={styles.container}>

      {/* ── 1. Decisión — lo primero que lees ── */}
      <Text style={[styles.recommendation, { color: zc }]}>
        {data.recommendation}
      </Text>

      {/* ── 2. Score — el argumento detrás de la decisión ── */}
      <View style={[styles.circle, { borderColor: zc, backgroundColor: zbg }]}>
        <Text style={[styles.scoreNum, { color: zc }]}>
          {data.recoveryScore}
        </Text>
        <Text style={[styles.zoneLabel, { color: zc }]}>
          {zn.toUpperCase()}
        </Text>
      </View>

      {/* ── 3. Confidence — solo visible si los datos son parciales ── */}
      {data.confidenceScore < 80 && (
        <View style={styles.confidenceBadge}>
          <Text style={styles.confidenceText}>
            ⚠️  Datos parciales · {data.confidenceScore}% confianza
          </Text>
        </View>
      )}

      {/* ── 4. Desglose Recovery / Balance / Strain ── */}
      <View style={styles.rsRow}>

        <View style={styles.rsSide}>
          <Text style={styles.rsLabel}>RECOVERY</Text>
          <Text style={[styles.rsValue, { color: Colors.purple }]}>
            {data.recoveryScore}
          </Text>
          <View style={styles.rsBarWrap}>
            <View
              style={[
                styles.rsBar,
                { width: `${data.recoveryScore}%`, backgroundColor: Colors.purple },
              ]}
            />
          </View>
        </View>

        <View style={styles.rsCenter}>
          <Text style={styles.rsCenterLabel}>BAL</Text>
          <Text style={[styles.rsCenterValue, { color: zc }]}>
            {data.balanceScore > 0 ? `+${data.balanceScore}` : data.balanceScore}
          </Text>
        </View>

        <View style={[styles.rsSide, styles.rsRight]}>
          <Text style={[styles.rsLabel, { textAlign: 'right' }]}>STRAIN</Text>
          <Text style={[styles.rsValue, { color: Colors.text2, textAlign: 'right' }]}>
            {data.strainScore}
          </Text>
          <View style={styles.rsBarWrap}>
            <View
              style={[
                styles.rsBar,
                { width: `${data.strainScore}%`, backgroundColor: Colors.text2 },
              ]}
            />
          </View>
        </View>

      </View>

    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: 28,
    paddingBottom: 8,
    alignItems: 'center',
    gap: 0,
  },

  // ── 1. Decisión ──
  recommendation: {
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: -0.8,
    textAlign: 'center',
    paddingHorizontal: 32,
    marginBottom: 20,
    lineHeight: 34,
  },

  // ── 2. Círculo ──
  circle: {
    width: 156,
    height: 156,
    borderRadius: 78,
    borderWidth: 7,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    // Sombra sutil
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 8,
  },
  scoreNum: {
    fontSize: 62,
    fontWeight: '900',
    letterSpacing: -3,
    lineHeight: 66,
  },
  zoneLabel: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.4,
    marginTop: 4,
  },

  // ── 3. Confidence badge ──
  confidenceBadge: {
    backgroundColor: 'rgba(255,204,0,0.07)',
    borderWidth: 1,
    borderColor: 'rgba(255,204,0,0.18)',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 5,
    marginBottom: 16,
  },
  confidenceText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.yellow,
  },

  // ── 4. RS Row ──
  rsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 16,
    width: '92%',
  },
  rsSide: {
    flex: 1,
  },
  rsRight: {
    alignItems: 'flex-end',
  },
  rsLabel: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.6,
    color: Colors.text3,
    marginBottom: 5,
    textTransform: 'uppercase',
  },
  rsValue: {
    fontSize: 32,
    fontWeight: '900',
    letterSpacing: -2,
    lineHeight: 34,
  },
  rsBarWrap: {
    height: 2,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 1,
    marginTop: 8,
    overflow: 'hidden',
  },
  rsBar: {
    height: '100%',
    borderRadius: 1,
  },
  rsCenter: {
    minWidth: 60,
    alignItems: 'center',
    paddingHorizontal: 8,
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    marginHorizontal: 4,
  },
  rsCenterLabel: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.6,
    color: Colors.text3,
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  rsCenterValue: {
    fontSize: 20,
    fontWeight: '900',
    lineHeight: 22,
  },
});
