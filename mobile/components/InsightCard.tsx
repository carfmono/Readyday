/**
 * ReadyDay — InsightCard (refined)
 *
 * El insight habla por sí solo — sin etiqueta, sin ruido.
 * El acento morado izquierdo da contexto visual suficiente.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../constants/colors';

interface Props {
  insight: string;
}

export function InsightCard({ insight }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.text}>{insight}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginBottom: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderRadius: 14,
    borderLeftWidth: 3,
    borderLeftColor: 'rgba(124,110,255,0.55)',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  text: {
    fontSize: 14,
    lineHeight: 22,
    color: 'rgba(240,240,250,0.82)',
    fontWeight: '500',
  },
});
