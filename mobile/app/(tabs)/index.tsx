/**
 * ReadyDay — Today Screen
 * Pantalla principal: consume /scores/today y renderiza todos los bloques.
 * Orden visual = HTML MVP: Score → Insight → Prediction → Factors
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  StyleSheet,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import type { DailyReadiness } from '../../../shared-types/readiness';
import { fetchToday } from '../../services/api';
import { ScoreCard }     from '../../components/ScoreCard';
import { InsightCard }   from '../../components/InsightCard';
import { PredictionCard } from '../../components/PredictionCard';
import { FactorsList }   from '../../components/FactorsList';
import { Colors }        from '../../constants/colors';

// ─────────────────────────────────────────────
// SCREEN
// ─────────────────────────────────────────────

export default function TodayScreen() {
  const [data,       setData]       = useState<DailyReadiness | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error,      setError]      = useState<string | null>(null);

  // ── Cargar datos ──────────────────────────
  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else           setLoading(true);
    setError(null);

    try {
      const result = await fetchToday('es');
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error desconocido');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Recargar cada vez que la tab recibe el foco
  useFocusEffect(useCallback(() => { load(); }, [load]));

  // ── Estados intermedios ───────────────────
  if (loading && !data) return <LoadingView />;
  if (error   && !data) return <ErrorView message={error} onRetry={() => load()} />;

  return (
    <SafeAreaView style={styles.root} edges={['top']}>

      {/* ── Header ── */}
      <Header />

      {/* ── Contenido ── */}
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => load(true)}
            tintColor={Colors.purple}
            colors={[Colors.purple]}
          />
        }
      >
        {data && (
          <>
            {/* 1. Score + Recommendation + RS Row */}
            <ScoreCard data={data} />

            {/* Separador sutil */}
            <View style={styles.divider} />

            {/* 2. Insight */}
            <InsightCard insight={data.insight} />

            {/* 3. Prediction (solo si el flag lo activa en el backend) */}
            {data.prediction && (
              <PredictionCard prediction={data.prediction} />
            )}

            {/* Separador sutil antes de factores */}
            <View style={styles.dividerSlim} />

            {/* 4. Top Factors */}
            <FactorsList
              topFactors={data.topFactors}
              factorExplanations={data.factorExplanations}
            />

            {/* Espacio inferior */}
            <View style={{ height: 24 }} />
          </>
        )}
      </ScrollView>

    </SafeAreaView>
  );
}

// ─────────────────────────────────────────────
// SUBCOMPONENTES
// ─────────────────────────────────────────────

function Header() {
  const today = new Date().toLocaleDateString('es-ES', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <View style={styles.header}>
      <Text style={styles.headerLogo}>
        Ready<Text style={styles.headerLogoAccent}>Day</Text>
      </Text>
      <Text style={styles.headerDate}>{today}</Text>
    </View>
  );
}

function LoadingView() {
  return (
    <SafeAreaView style={styles.center}>
      <ActivityIndicator size="large" color={Colors.purple} />
      <Text style={styles.loadingText}>Calculando tu día…</Text>
    </SafeAreaView>
  );
}

function ErrorView({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <SafeAreaView style={styles.center}>
      <Text style={styles.errorIcon}>⚠️</Text>
      <Text style={styles.errorTitle}>Sin conexión</Text>
      <Text style={styles.errorMessage}>{message}</Text>
      <Pressable style={styles.retryBtn} onPress={onRetry}>
        <Text style={styles.retryText}>Reintentar</Text>
      </Pressable>
      <Text style={styles.errorHint}>
        Asegúrate de que el backend está corriendo:{'\n'}
        cd backend && uvicorn main:app --reload
      </Text>
    </SafeAreaView>
  );
}

// ─────────────────────────────────────────────
// STYLES
// ─────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.bg,
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    backgroundColor: 'rgba(7,7,15,0.88)',
  },
  headerLogo: {
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: -0.3,
    color: Colors.text,
  },
  headerLogoAccent: {
    color: Colors.purple,
  },
  headerDate: {
    fontSize: 11,
    color: Colors.text2,
    textTransform: 'capitalize',
  },

  // Scroll
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: 4,
  },

  // Separadores de sección
  divider: {
    height: 1,
    backgroundColor: Colors.border,
    marginHorizontal: 16,
    marginTop: 4,
    marginBottom: 14,
    opacity: 0.6,
  },
  dividerSlim: {
    height: 1,
    backgroundColor: Colors.border,
    marginHorizontal: 16,
    marginTop: 4,
    marginBottom: 14,
    opacity: 0.4,
  },

  // Loading
  center: {
    flex: 1,
    backgroundColor: Colors.bg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 14,
    fontSize: 14,
    color: Colors.text2,
    fontWeight: '600',
  },

  // Error
  errorIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.text,
    marginBottom: 8,
  },
  errorMessage: {
    fontSize: 13,
    color: Colors.text2,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 18,
  },
  retryBtn: {
    backgroundColor: Colors.purple,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    marginBottom: 20,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#fff',
  },
  errorHint: {
    fontSize: 11,
    color: Colors.text3,
    textAlign: 'center',
    lineHeight: 18,
    fontFamily: 'monospace',
  },
});
