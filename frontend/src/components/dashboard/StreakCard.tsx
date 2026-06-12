// src/components/dashboard/StreakCard.tsx
import React from 'react';
import { View, Text } from 'react-native';

interface StreakCardProps {
  currentStreak?: number;
}

export function StreakCard({ currentStreak = 13 }: StreakCardProps) {
  return (
    <View style={{ paddingHorizontal: 24, marginBottom: 20 }}>
      <Text style={{ fontSize: 17, fontWeight: 'bold', color: '#1E1E2F', marginBottom: 12 }}>
        Racha de tutorías
      </Text>
      
      <View style={{
        backgroundColor: 'white',
        borderRadius: 16,
        padding: 20,
        borderWidth: 1,
        borderColor: '#EEEDFE',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 8,
        elevation: 2,
        alignItems: 'center',
      }}>
        <Text style={{ fontSize: 40, marginBottom: 8, textAlign: 'center' }}>🔥</Text>
        <Text style={{
          color: '#F97316',
          fontWeight: '800',
          fontSize: 22,
          letterSpacing: -0.5,
          textAlign: 'center',
        }}>
          ¡{currentStreak} días de racha!
        </Text>
        <Text style={{
          color: '#8E8EA0',
          fontSize: 12,
          fontWeight: '600',
          textAlign: 'center',
          marginTop: 6,
          paddingHorizontal: 16,
          lineHeight: 16,
        }}>
          Completa tu siguiente tutoría para aumentar tu racha
        </Text>
      </View>
    </View>
  );
}
