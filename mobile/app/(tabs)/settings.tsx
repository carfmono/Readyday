/**
 * ReadyDay — Settings Screen (Sprint 3)
 * Hábitos por defecto + override del día.
 * Conecta con GET/PATCH /defaults y PUT /overrides/today
 */

import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  Switch,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import { Colors } from '../../constants/colors';

// ─────────────────────────────────────────────
// API helpers (sin usecase layer todavía)
// ─────────────────────────────────────────────

const API = (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

async function getDefaults() {
  const r = await fetch(`${API}/defaults`);
  const j = await r.json();
  return j.data as Defaults;
}

async function patchDefaults(patch: Partial<Defaults>) {
  const r = await fetch(`${API}/defaults`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
  if (!r.ok) throw new Error('Error guardando defaults');
  return (await r.json()).data as Defaults;
}

async function getTodayOverride() {
  const r = await fetch(`${API}/overrides/today`);
  const j = await r.json();
  return (j.data ?? {}) as Partial<Override>;
}

async function putTodayOverride(body: Partial<Override>) {
  const r = await fetch(`${API}/overrides/today`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error('Error guardando override');
  return (await r.json()).data as Partial<Override>;
}

// ─────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────

type Defaults = {
  caffeineLate: { cups: number; lastTime: string | null };
  alcohol: { drinks: number };
  lateDinner: { ate: boolean; time: string | null };
};

type Override = Defaults & { energyManual: number | null };

const EMPTY_DEFAULTS: Defaults = {
  caffeineLate: { cups: 0, lastTime: null },
  alcohol: { drinks: 0 },
  lateDinner: { ate: false, time: null },
};

// ─────────────────────────────────────────────
// SUBCOMPONENTS
// ─────────────────────────────────────────────

function SectionTitle({ title }: { title: string }) {
  return <Text style={styles.sectionTitle}>{title}</Text>;
}

/** Toggle row genérico */
function ToggleRow({
  icon,
  label,
  desc,
  value,
  onChange,
}: {
  icon: string;
  label: string;
  desc?: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <View style={styles.toggleRow}>
      <Text style={styles.toggleIcon}>{icon}</Text>
      <View style={styles.toggleBody}>
        <Text style={styles.toggleLabel}>{label}</Text>
        {desc && <Text style={styles.toggleDesc}>{desc}</Text>}
      </View>
      <Switch
        value={value}
        onValueChange={onChange}
        trackColor={{ false: Colors.card2, true: Colors.purple }}
        thumbColor="#fff"
      />
    </View>
  );
}

/** Counter row para cups/drinks */
function CounterRow({
  icon,
  label,
  value,
  onDecr,
  onIncr,
  max,
}: {
  icon: string;
  label: string;
  value: number;
  onDecr: () => void;
  onIncr: () => void;
  max: number;
}) {
  return (
    <View style={styles.counterRow}>
      <Text style={styles.toggleIcon}>{icon}</Text>
      <View style={styles.toggleBody}>
        <Text style={styles.toggleLabel}>{label}</Text>
      </View>
      <View style={styles.counterControls}>
        <TouchableOpacity
          style={[styles.counterBtn, value === 0 && styles.counterBtnDisabled]}
          onPress={onDecr}
          disabled={value === 0}
        >
          <Text style={styles.counterBtnText}>−</Text>
        </TouchableOpacity>
        <Text style={styles.counterVal}>{value}</Text>
        <TouchableOpacity
          style={[styles.counterBtn, value >= max && styles.counterBtnDisabled]}
          onPress={onIncr}
          disabled={value >= max}
        >
          <Text style={styles.counterBtnText}>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

/** Guardando indicador */
function SaveIndicator({ saving }: { saving: boolean }) {
  if (!saving) return null;
  return (
    <View style={styles.saveIndicator}>
      <ActivityIndicator size="small" color={Colors.purple} />
      <Text style={styles.saveText}>Guardando…</Text>
    </View>
  );
}

// ─────────────────────────────────────────────
// SCREEN
// ─────────────────────────────────────────────

export default function SettingsScreen() {
  const [defaults,   setDefaults]   = useState<Defaults>(EMPTY_DEFAULTS);
  const [override,   setOverride]   = useState<Partial<Override>>({});
  const [loading,    setLoading]    = useState(true);
  const [saving,     setSaving]     = useState(false);
  const [error,      setError]      = useState<string | null>(null);

  // ── Cargar al enfocar ──
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [d, o] = await Promise.all([getDefaults(), getTodayOverride()]);
      setDefaults(d);
      setOverride(o);
    } catch (e: any) {
      setError(e.message ?? 'Error cargando ajustes');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  // ── Guardar defaults automáticamente ──
  const saveDefaults = useCallback(async (next: Defaults) => {
    setDefaults(next);
    setSaving(true);
    try {
      await patchDefaults(next);
    } catch {
      Alert.alert('Error', 'No se pudo guardar. Revisa la conexión.');
    } finally {
      setSaving(false);
    }
  }, []);

  // ── Guardar override del día ──
  const saveOverride = useCallback(async (next: Partial<Override>) => {
    setOverride(next);
    setSaving(true);
    try {
      await putTodayOverride(next);
    } catch {
      Alert.alert('Error', 'No se pudo guardar el override de hoy.');
    } finally {
      setSaving(false);
    }
  }, []);

  // ── Helpers de defaults ──
  const defCups   = defaults.caffeineLate?.cups   ?? 0;
  const defDrinks = defaults.alcohol?.drinks      ?? 0;
  const defDinner = defaults.lateDinner?.ate      ?? false;

  // ── Helpers de override ──
  const ovCups    = override.caffeineLate?.cups   ?? defCups;
  const ovDrinks  = override.alcohol?.drinks      ?? defDrinks;
  const ovDinner  = override.lateDinner?.ate      ?? defDinner;

  if (loading) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator size="large" color={Colors.purple} />
        <Text style={styles.loadingText}>Cargando ajustes…</Text>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.center}>
        <Text style={{ fontSize: 36 }}>⚠️</Text>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryBtn} onPress={load}>
          <Text style={styles.retryText}>Reintentar</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.root} edges={['top']}>

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.logo}>
          Ready<Text style={styles.accent}>Day</Text>
        </Text>
        <SaveIndicator saving={saving} />
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >

        {/* ── HÁBITOS POR DEFECTO ── */}
        <SectionTitle title="HÁBITOS HABITUALES" />
        <Text style={styles.sectionDesc}>
          Tus patrones normales. Se usan en el cálculo diario si no los cambias.
        </Text>

        <View style={styles.card}>
          <CounterRow
            icon="☕"
            label="Cafés tarde al día"
            value={defCups}
            max={5}
            onDecr={() => saveDefaults({ ...defaults, caffeineLate: { ...defaults.caffeineLate, cups: Math.max(0, defCups - 1) } })}
            onIncr={() => saveDefaults({ ...defaults, caffeineLate: { ...defaults.caffeineLate, cups: Math.min(5, defCups + 1) } })}
          />
          <View style={styles.cardDivider} />
          <CounterRow
            icon="🍺"
            label="Bebidas alcohólicas"
            value={defDrinks}
            max={5}
            onDecr={() => saveDefaults({ ...defaults, alcohol: { drinks: Math.max(0, defDrinks - 1) } })}
            onIncr={() => saveDefaults({ ...defaults, alcohol: { drinks: Math.min(5, defDrinks + 1) } })}
          />
          <View style={styles.cardDivider} />
          <ToggleRow
            icon="🌙"
            label="Cena después de las 21h"
            desc="Cenas tardías frecuentes"
            value={defDinner}
            onChange={(v) => saveDefaults({ ...defaults, lateDinner: { ...defaults.lateDinner, ate: v } })}
          />
        </View>

        {/* ── OVERRIDE DEL DÍA ── */}
        <SectionTitle title="HOY FUE DIFERENTE" />
        <Text style={styles.sectionDesc}>
          Ajusta si ayer tus hábitos fueron distintos a lo normal. Afecta solo el cálculo de hoy.
        </Text>

        <View style={styles.card}>
          <CounterRow
            icon="☕"
            label="Cafés tarde (ayer)"
            value={ovCups}
            max={5}
            onDecr={() => saveOverride({ ...override, caffeineLate: { cups: Math.max(0, ovCups - 1), lastTime: null } })}
            onIncr={() => saveOverride({ ...override, caffeineLate: { cups: Math.min(5, ovCups + 1), lastTime: null } })}
          />
          <View style={styles.cardDivider} />
          <CounterRow
            icon="🍺"
            label="Bebidas alcohólicas (ayer)"
            value={ovDrinks}
            max={5}
            onDecr={() => saveOverride({ ...override, alcohol: { drinks: Math.max(0, ovDrinks - 1) } })}
            onIncr={() => saveOverride({ ...override, alcohol: { drinks: Math.min(5, ovDrinks + 1) } })}
          />
          <View style={styles.cardDivider} />
          <ToggleRow
            icon="🌙"
            label="Cena tarde (ayer)"
            value={ovDinner}
            onChange={(v) => saveOverride({ ...override, lateDinner: { ate: v, time: v ? '22:00' : null } })}
          />
        </View>

        {/* ── APP INFO ── */}
        <SectionTitle title="APP" />
        <View style={styles.card}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Versión</Text>
            <Text style={styles.infoValue}>0.1.0 · Sprint 3</Text>
          </View>
          <View style={styles.cardDivider} />
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Backend</Text>
            <Text style={styles.infoValue}>{API}</Text>
          </View>
          <View style={styles.cardDivider} />
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Know your body.</Text>
            <Text style={styles.infoValue}>Decide your day. 🟢</Text>
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
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

  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 16, paddingTop: 20 },

  sectionTitle: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.2,
    color: Colors.text3,
    textTransform: 'uppercase',
    marginBottom: 4,
    marginLeft: 2,
  },
  sectionDesc: {
    fontSize: 12,
    color: Colors.text2,
    lineHeight: 17,
    marginBottom: 10,
    marginLeft: 2,
  },

  card: {
    backgroundColor: Colors.card,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 16,
    marginBottom: 24,
    overflow: 'hidden',
  },
  cardDivider: {
    height: 1,
    backgroundColor: Colors.border,
    marginHorizontal: 14,
  },

  // Toggle row
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 14,
    gap: 12,
  },
  toggleIcon: { fontSize: 20, width: 28, textAlign: 'center' },
  toggleBody: { flex: 1 },
  toggleLabel: { fontSize: 14, fontWeight: '600', color: Colors.text },
  toggleDesc: { fontSize: 11, color: Colors.text2, marginTop: 1 },

  // Counter row
  counterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 14,
    gap: 12,
  },
  counterControls: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  counterBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(124,110,255,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(124,110,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  counterBtnDisabled: { opacity: 0.3 },
  counterBtnText: { fontSize: 18, fontWeight: '700', color: Colors.purple, lineHeight: 22 },
  counterVal: { fontSize: 18, fontWeight: '900', color: Colors.text, minWidth: 24, textAlign: 'center' },

  // Info row
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  infoLabel: { fontSize: 14, color: Colors.text2, fontWeight: '500' },
  infoValue: { fontSize: 12, color: Colors.text3, fontWeight: '600' },

  // Save indicator
  saveIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  saveText: { fontSize: 11, color: Colors.purple, fontWeight: '600' },

  // States
  center: { flex: 1, backgroundColor: Colors.bg, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingText: { fontSize: 13, color: Colors.text2 },
  errorText: { fontSize: 13, color: Colors.text2, textAlign: 'center', paddingHorizontal: 32 },
  retryBtn: {
    paddingHorizontal: 20, paddingVertical: 10,
    backgroundColor: 'rgba(124,110,255,0.15)',
    borderRadius: 20, borderWidth: 1, borderColor: 'rgba(124,110,255,0.3)',
  },
  retryText: { fontSize: 13, fontWeight: '700', color: Colors.purple },
});
