/**
 * ReadyDay — Settings Screen (Sprint 3)
 * Placeholder — idioma, objetivo, hábitos defaults en Sprint 3.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/colors';

export default function SettingsScreen() {
  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.title}>
          Ready<Text style={styles.accent}>Day</Text>
        </Text>
        <Text style={styles.subtitle}>Ajustes</Text>
      </View>

      <View style={styles.body}>
        <Text style={styles.icon}>⚙️</Text>
        <Text style={styles.label}>Disponible en Sprint 3</Text>
        <Text style={styles.desc}>
          Idioma · Objetivo · Hábitos por defecto
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
