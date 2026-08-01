import React from 'react';
import { View, Text, Pressable, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/src/theme/ThemeContext';

interface CalendarLoadStateProps {
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  children: React.ReactNode;
}

/**
 * Estado de carga del calendario compartido por las pantallas de estudiante y tutor.
 *
 * fetchSessions y fetchTutorData reportan sus fallos con notify:false, de modo que la
 * unica senal que recibe la persona usuaria es este bloque. Si una pantalla no lo
 * renderiza, el error queda invisible: el calendario aparece vacio sin explicacion.
 */
export function CalendarLoadState({ isLoading, error, onRetry, children }: CalendarLoadStateProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();

  if (isLoading) {
    return <ActivityIndicator color={colors.primary} style={{ marginTop: 40 }} />;
  }

  if (error) {
    return (
      <View
        style={{
          backgroundColor: colors.surface,
          marginHorizontal: 24,
          padding: 24,
          borderRadius: 16,
          alignItems: 'center',
          borderWidth: 1,
          borderColor: colors.border,
          marginTop: 20,
        }}
      >
        <Feather name="alert-circle" size={32} color={colors.danger} style={{ marginBottom: 10 }} />
        <Text style={{ color: colors.text, textAlign: 'center', marginBottom: 16 }}>{error}</Text>
        <Pressable
          onPress={onRetry}
          style={{
            backgroundColor: colors.primary,
            paddingHorizontal: 20,
            paddingVertical: 10,
            borderRadius: 12,
          }}
        >
          <Text style={{ color: 'white', fontWeight: 'bold' }}>{t('common.retry')}</Text>
        </Pressable>
      </View>
    );
  }

  return <>{children}</>;
}
