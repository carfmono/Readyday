/**
 * ReadyDay — PredictionCard
 * Bloque 🔮 con predicción de mañana.
 * Replica .pred-card del HTML MVP.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../constants/colors';

interface Props {
  prediction: string;
}

export function PredictionCard({ prediction }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.icon}>🔮</Text>
      <View style={styles.body}>
        <Text style={styles.label}>PREDICCIÓN</Text>
        <Text style={styles.text}>{prediction}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginBottom: 10,
    padding: 14,
    backgroundColor: 'rgba(124,110,255,0.05)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(124,110,255,0.18)',
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  icon: {
    fontSize: 18,
    marginTop: 1,
  },
  body: {
    flex: 1,
  },
  label: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    color: Colors.purple,
    marginBottom: 4,
  },
  text: {
    fontSize: 13,
    lineHeight: 20,
    color: 'rgba(240,240,250,0.7)',
    fontWeight: '500',
  },
});
