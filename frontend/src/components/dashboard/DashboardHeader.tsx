import React from 'react';
import { View, Text } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

interface DashboardHeaderProps {
  firstName: string;
}

export function DashboardHeader({ firstName }: DashboardHeaderProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);

  return (
    <View style={{
      paddingTop: paddingTop + 10,
      paddingBottom: 12,
      paddingHorizontal: 24,
    }}>
      <Text style={{
        fontSize: 28,
        fontWeight: 'bold',
        color: colors.text,
        letterSpacing: -0.5,
      }}>
        {t('dashboard.greeting', { name: firstName })}
      </Text>
      <Text style={{
        fontSize: 14,
        color: colors.textSecondary,
        marginTop: 4,
        fontWeight: '500',
      }}>
        {t('dashboard.subtitle')}
      </Text>
    </View>
  );
}
