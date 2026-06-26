// src/components/dashboard/StreakCard.tsx
import React, { useState, useEffect } from 'react';
import { View, Text } from 'react-native';
import { useTheme } from '@/src/theme/ThemeContext';
import { QuotesAPI } from '@/src/api/services';

interface StreakCardProps {
  currentStreak?: number;
}



export function StreakCard({ currentStreak = 13 }: StreakCardProps) {
  const { colors } = useTheme();
  const [quote, setQuote] = useState("");

  useEffect(() => {
    QuotesAPI.getRandomQuote().then(q => {
      setQuote(q.text);
    }).catch(err => {
      console.error("Failed to load quote:", err);
      setQuote("Cree en ti mismo y en lo que eres.");
    });
  }, []);

  return (
    <View style={{ paddingHorizontal: 24, marginBottom: 20 }}>
      <Text style={{ fontSize: 17, fontWeight: 'bold', color: colors.text, marginBottom: 12 }}>
        Racha de tutorías
      </Text>
      
      <View style={{
        backgroundColor: colors.surface,
        borderRadius: 16,
        padding: 20,
        borderWidth: 1,
        borderColor: colors.border,
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
          color: colors.textSecondary,
          fontSize: 12,
          fontWeight: '600',
          textAlign: 'center',
          marginTop: 6,
          paddingHorizontal: 16,
          lineHeight: 16,
        }}>
          Completa tu siguiente tutoría para aumentar tu racha
        </Text>

        {quote ? (
          <View style={{
            marginTop: 16,
            paddingTop: 16,
            borderTopWidth: 1,
            borderTopColor: colors.border,
            width: '100%',
          }}>
            <Text style={{
              color: colors.primary,
              fontSize: 13,
              fontStyle: 'italic',
              fontWeight: '500',
              textAlign: 'center',
              lineHeight: 18,
            }}>
              "{quote}"
            </Text>
          </View>
        ) : null}
      </View>
    </View>
  );
}
