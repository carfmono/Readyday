/**
 * ReadyDay — Trends Screen (Sprint 3)
 * Placeholder — implementación completa en Sprint 3 con datos reales.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/colors';

export default function TrendsScreen() {
  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.title}>
          Ready<Text style={styles.accent}>Day</Text>
        </Text>
        <Text style={styles.subtitle}>Tendencias · 7 días</Text>
      </View>

      <View style={styles.body}>
        <Text style={styles.icon}>📊</Text>
        <Text style={styles.label}>Disponible en Sprint 3</Text>
        <Text style={styles.desc}>
          Recovery 7d · Strain 7d · Score 7d
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.bg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  title: {
    fontSize: 16,
    fontWeight: '900',
    color: Colors.text,
  },
  accent: {
    color: Colors.purple,
  },
  subtitle: {
    fontSize: 11,
    color: Colors.text2,
  },
  body: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  icon: {
    fontSize: 40,
    marginBottom: 4,
  },
  label: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.text2,
  },
  desc: {
    fontSize: 12,
    color: Colors.text3,
  },
});
