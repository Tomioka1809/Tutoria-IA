// src/components/calendar/CalendarHeader.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text } from 'react-native';

export function CalendarHeader() {
  const { colors } = useTheme();
  return (
    <View className="px-6 items-center mb-6">
      <Text style={{ color: colors.text }} className="text-[20px] font-bold ">Calendario</Text>
    </View>
  );
}
