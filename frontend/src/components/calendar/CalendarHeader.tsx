// src/components/calendar/CalendarHeader.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text } from 'react-native';
import { useTranslation } from 'react-i18next';

export function CalendarHeader() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  return (
    <View className="px-6 items-center mb-6">
      <Text style={{ color: colors.text }} className="text-[20px] font-bold ">{t('calendar.title')}</Text>
    </View>
  );
}
