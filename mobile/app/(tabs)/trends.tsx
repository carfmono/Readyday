/**
 * ReadyDay — Trends Screen (Sprint 3)
 * Historial 7/30 días: Recovery · Strain · Balance por día.
 * Datos reales desde GET /scores/history
 */

import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { Colors, zoneColor } from '../../constants/colors';
import { fetchHistory } from '../../services/api';
import type { DailyReadiness } from '../../../shared-types/readiness';

// ─────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────

function shortDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('es-CO', { weekday: 'short', day: 'numeric' });
}

function avg(arr: number[]): number {
  if (!arr.length) return 0;
  return Math.round(arr.reduce((a, b) => a + b, 0) / arr.length);
}

// ─────────────────────────────────────────────
// BAR CHART
// ─────────────────────────────────────────────

function BarChart({
  data,
  valueKey,
  color,
}: {
  data: DailyReadiness[];
  valueKey: 'recoveryScore' | 'strainScore' | 'balanceScore';
  color: string;
}) {
  const MAX_H = 80;
  const values = data.map(d => d[valueKey] ?? 0);
  const maxVal = Math.max(...values, 1);
  const minVal = Math.min(...values, 0);
  const range  = maxVal - minVal || 1;

  return (
    <View style={styles.chartWrap}>
      {data.map((d, i) => {
        const raw = d[valueKey] ?? 0;
        // Para balance puede ser negativo
        const pct = valueKey === 'balanceScore'
          ? Math.max(0, (raw - minVal) / range)
          : raw / 100;
        const barH = Math.max(4, Math.round(pct * MAX_H));
        const isToday = i === data.length - 1;
        const zc = zoneColor(d.zone);

        return (
          <View key={d.date} style={styles.barCol}>
            <Text style={styles.barVal} numberOfLines={1}>
              {raw > 0 ? '+' : ''}{raw}
            </Text>
            <View style={[styles.barTrack, { height: MAX_H }]}>
              <View
                style={[
                  styles.barFill,
                  {
                    height: barH,
                    backgroundColor: isToday ? zc : color,
                    opacity: isToday ? 1 : 0.55,
                  },
                ]}
              />
            </View>
            <Text style={[styles.barDate, isToday && { color: Colors.purple }]}>
              {shortDate(d.date)}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

// ─────────────────────────────────────────────
// STAT SUMMARY
// ─────────────────────────────────────────────

function StatSummary({ data }: { data: DailyReadiness[] }) {
  const recoveries = data.map(d => d.recoveryScore);
  const strains    = data.map(d => d.strainScore);
  const greens     = data.filter(d => d.zone === 'green').length;
  const yellows    = data.filter(d => d.zone === 'yellow').length;
  const reds       = data.filter(d => d.zone === 'red').length;

  return (
    <View style={styles.summaryRow}>
      <View style={styles.summaryCard}>
        <Text style={[styles.summaryNum, { color: Colors.purple }]}>{avg(recoveries)}</Text>
        <Text style={styles.summaryLbl}>Recovery{'\n'}promedio</Text>
      </View>
      <View style={styles.summaryCard}>
        <Text style={[styles.summaryNum, { color: Colors.text2 }]}>{avg(strains)}</Text>
        <Text style={styles.summaryLbl}>Strain{'\n'}promedio</Text>
      </View>
      <View style={styles.summaryCard}>
        <Text style={styles.summaryZones}>
          <Text style={{ color: Colors.green }}>●{greens} </Text>
          <Text style={{ color: Colors.yellow }}>●{yellows} </Text>
          <Text style={{ color: Colors.red }}>●{reds}</Text>
        </Text>
        <Text style={styles.summaryLbl}>Zonas{'\n'}(V/M/R)</Text>
      </View>
    </View>
  );
}

// ─────────────────────────────────────────────
// SCREEN
// ─────────────────────────────────────────────

type Window = 7 | 14 | 30;

export default function TrendsScreen() {
  const [data,       setData]       = useState<DailyReadiness[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error,      setError]      = useState<string | null>(null);
  const [window,     setWindow]     = useState<Window>(7);

  const load = useCallback(async (days: Window, isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else           setLoading(true);
    setError(null);
    try {
      const history = await fetchHistory(days);
      // Ordenar cronológicamente (más antiguo primero) para el gráfico
      const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));
      setData(sorted);
    } catch (e: any) {
      setError(e.message ?? 'Error al cargar historial');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(window); }, [window, load]));

  const hasData = data.length > 0;

  return (
    <SafeAreaView style={styles.root} edges={['top']}>

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.logo}>
          Ready<Text style={styles.accent}>Day</Text>
        </Text>
        <View style={styles.windowPicker}>
          {([7, 14, 30] as Window[]).map(w => (
            <TouchableOpacity
              key={w}
              style={[styles.windowBtn, window === w && styles.windowBtnActive]}
              onPress={() => setWindow(w)}
            >
              <Text style={[styles.windowBtnText, window === w && styles.windowBtnTextActive]}>
                {w}d
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Loading */}
      {loading && (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.purple} />
          <Text style={styles.loadingText}>Cargando historial…</Text>
        </View>
      )}

      {/* Error */}
      {!loading && error && (
        <View style={styles.center}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={() => load(window)}>
            <Text style={styles.retryText}>Reintentar</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Sin datos */}
      {!loading && !error && !hasData && (
        <View style={styles.center}>
          <Text style={{ fontSize: 36 }}>📭</Text>
          <Text style={styles.emptyText}>
            Sin historial aún.{'\n'}Los datos aparecen después del primer día.
          </Text>
        </View>
      )}

      {/* Datos */}
      {!loading && !error && hasData && (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => load(window, true)}
              tintColor={Colors.purple}
            />
          }
        >
          {/* Resumen estadístico */}
          <StatSummary data={data} />

          {/* Chart: Recovery */}
          <View style={styles.chartSection}>
            <Text style={styles.chartTitle}>
              <Text style={{ color: Colors.purple }}>■ </Text>RECOVERY
            </Text>
            <BarChart data={data} valueKey="recoveryScore" color={Colors.purple} />
          </View>

          {/* Chart: Strain */}
          <View style={styles.chartSection}>
            <Text style={styles.chartTitle}>
              <Text style={{ color: Colors.text2 }}>■ </Text>STRAIN
            </Text>
            <BarChart data={data} valueKey="strainScore" color={Colors.text2} />
          </View>

          {/* Chart: Balance */}
          <View style={styles.chartSection}>
            <Text style={styles.chartTitle}>
              <Text style={{ color: Colors.green }}>■ </Text>BALANCE
            </Text>
            <BarChart data={data} valueKey="balanceScore" color={Colors.green} />
          </View>

          {/* Tabla detallada */}
          <View style={styles.tableSection}>
            <Text style={styles.tableSectionTitle}>DETALLE POR DÍA</Text>
            {[...data].reverse().map((d) => {
              const zc = zoneColor(d.zone);
              return (
                <View key={d.date} style={styles.tableRow}>
                  <View style={[styles.tableZoneDot, { backgroundColor: zc }]} />
                  <Text style={styles.tableDate}>{shortDate(d.date)}</Text>
                  <View style={styles.tableCols}>
                    <Text style={[styles.tableVal, { color: Colors.purple }]}>
                      R {d.recoveryScore}
                    </Text>
                    <Text style={[styles.tableVal, { color: Colors.text2 }]}>
                      S {d.strainScore}
                    </Text>
                    <Text style={[styles.tableVal, { color: zc }]}>
                      {d.recommendation}
                    </Text>
                  </View>
                </View>
              );
            })}
          </View>

          <View style={{ height: 24 }} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

// ─────────────────────────────────────────────
// STYLES
// ─────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.bg },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  logo: { fontSize: 16, fontWeight: '900', color: Colors.text, letterSpacing: -0.3 },
  accent: { color: Colors.purple },

  windowPicker: { flexDirection: 'row', gap: 6 },
  windowBtn: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.card,
  },
  windowBtnActive: {
    backgroundColor: 'rgba(124,110,255,0.15)',
    borderColor: 'rgba(124,110,255,0.4)',
  },
  windowBtnText: { fontSize: 12, fontWeight: '700', color: Colors.text2 },
  windowBtnTextActive: { color: Colors.purple },

  scroll: { flex: 1 },
  scrollContent: { paddingTop: 8 },

  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingText: { fontSize: 13, color: Colors.text2 },
  errorIcon: { fontSize: 36 },
  errorText: { fontSize: 13, color: Colors.text2, textAlign: 'center', paddingHorizontal: 32 },
  retryBtn: {
    paddingHorizontal: 20, paddingVertical: 10,
    backgroundColor: 'rgba(124,110,255,0.15)',
    borderRadius: 20, borderWidth: 1, borderColor: 'rgba(124,110,255,0.3)',
  },
  retryText: { fontSize: 13, fontWeight: '700', color: Colors.purple },
  emptyText: { fontSize: 13, color: Colors.text2, textAlign: 'center', lineHeight: 20, paddingHorizontal: 32 },

  // Summary
  summaryRow: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginBottom: 12,
    gap: 8,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: Colors.card,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 14,
    padding: 14,
    alignItems: 'center',
    gap: 4,
  },
  summaryNum: { fontSize: 28, fontWeight: '900', letterSpacing: -1 },
  summaryZones: { fontSize: 16, fontWeight: '700' },
  summaryLbl: { fontSize: 10, color: Colors.text2, textAlign: 'center', fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.3 },

  // Chart
  chartSection: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: Colors.card,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 16,
    padding: 16,
  },
  chartTitle: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    color: Colors.text3,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  chartWrap: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 6,
    justifyContent: 'space-between',
  },
  barCol: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
  },
  barVal: {
    fontSize: 8,
    fontWeight: '700',
    color: Colors.text3,
  },
  barTrack: {
    width: '100%',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 4,
    justifyContent: 'flex-end',
    overflow: 'hidden',
  },
  barFill: {
    width: '100%',
    borderRadius: 4,
  },
  barDate: {
    fontSize: 8,
    color: Colors.text3,
    fontWeight: '600',
    textAlign: 'center',
  },

  // Table
  tableSection: {
    marginHorizontal: 16,
    marginBottom: 8,
  },
  tableSectionTitle: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    color: Colors.text3,
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 14,
    backgroundColor: Colors.card,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 12,
    marginBottom: 7,
    gap: 10,
  },
  tableZoneDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    flexShrink: 0,
  },
  tableDate: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.text2,
    width: 56,
    textTransform: 'capitalize',
  },
  tableCols: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flexWrap: 'wrap',
  },
  tableVal: {
    fontSize: 11,
    fontWeight: '700',
  },
});
